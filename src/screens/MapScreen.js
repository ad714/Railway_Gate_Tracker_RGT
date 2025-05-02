import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { View, Text, StyleSheet, ActivityIndicator, Alert, Keyboard } from 'react-native';
import * as Location from 'expo-location';
import Constants from 'expo-constants';
import SearchComponent from '../components/SearchComponent';
import MapComponent from '../components/MapComponent';
import ButtonComponent from '../components/ButtonComponent';
import debounce from 'lodash.debounce';
import { fetchGates, sendDataToBackend } from '../utils'; // Import from utils

const MapScreen = ({ navigation }) => {
  const apiKey = Constants.expoConfig?.extra?.expoPublicGoogleMapsApiKey;
  const [userLocation, setUserLocation] = useState(null);
  const [region, setRegion] = useState(null);
  const [origin, setOrigin] = useState(null);
  const [destination, setDestination] = useState(null);
  const [search, setSearch] = useState('');
  const [predictions, setPredictions] = useState([]);
  const [predictionLoading, setPredictionLoading] = useState(false);
  const [routeCoordinates, setRouteCoordinates] = useState([]);
  const [gates, setGates] = useState([]);
  const [showGatesButton, setShowGatesButton] = useState(false);
  const [fetchingGates, setFetchingGates] = useState(false);
  const [sendingData, setSendingData] = useState(false);
  const [searchMode, setSearchMode] = useState('origin');
  const [selectedGate, setSelectedGate] = useState(null);
  const [isGateLoading, setIsGateLoading] = useState(false);
  const [tripMetadata, setTripMetadata] = useState({ duration: null, distance: null });
  const mapRef = useRef(null);

  useEffect(() => {
    (async () => {
      try {
        const { status } = await Location.requestForegroundPermissionsAsync();
        if (status !== 'granted') {
          Alert.alert('Location Permission Denied', 'Please enable location services.');
          return;
        }
        const location = await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.High, timeout: 10000 });
        const newLocation = {
          latitude: location.coords.latitude,
          longitude: location.coords.longitude,
          latitudeDelta: 0.0922,
          longitudeDelta: 0.0421,
        };
        console.log('Initial location:', newLocation);
        setUserLocation(newLocation);
        setRegion(newLocation);
        setOrigin(newLocation);
      } catch (error) {
        console.error('Location error:', error);
        Alert.alert('Error', 'Failed to fetch location.');
      }
    })();
  }, []);

  const debouncedFetchRoute = useCallback(
    debounce(async () => {
      if (!origin || !destination) return;
      try {
        console.log('Fetching route:', { origin, destination });
        const response = await fetch(
          `https://maps.googleapis.com/maps/api/directions/json?origin=${origin.latitude},${origin.longitude}&destination=${destination.latitude},${destination.longitude}&key=${apiKey}`
        );
        const data = await response.json();
        if (data.status === 'OK') {
          const points = data.routes[0].overview_polyline.points;
          const decodedPoints = decodePolyline(points);
          console.log('Route coordinates:', decodedPoints.length);
          setRouteCoordinates(decodedPoints);
          setTripMetadata({
            duration: data.routes[0].legs[0].duration.value,
            distance: data.routes[0].legs[0].distance.value,
          });
          setShowGatesButton(true);
          if (mapRef.current) {
            mapRef.current.fitToCoordinates([origin, destination], {
              edgePadding: { top: 100, right: 100, bottom: 100, left: 100 },
              animated: true,
            });
          }
        } else {
          console.error('Directions error:', data.status, data.error_message || 'Unknown error');
          Alert.alert('Error', 'Failed to fetch route.');
        }
      } catch (error) {
        console.error('Directions fetch error:', error.message);
        Alert.alert('Error', 'Network error occurred.');
      }
    }, 500),
    [origin, destination, apiKey]
  );

  useEffect(() => {
    debouncedFetchRoute();
    return () => debouncedFetchRoute.cancel();
  }, [origin, destination]);

  const fetchPlaceDetails = async (placeId) => {
    try {
      console.log('Fetching place details for place_id:', placeId);
      const response = await fetch(
        `https://maps.googleapis.com/maps/api/place/details/json?place_id=${placeId}&fields=geometry&key=${apiKey}`
      );
      const data = await response.json();
      console.log('Place details response:', JSON.stringify(data, null, 2));
      if (data.status === 'OK') {
        return data.result;
      } else {
        console.error('Place details error:', data.status, data.error_message || 'Unknown error');
        Alert.alert('Error', data.error_message || 'Failed to fetch place details.');
        return null;
      }
    } catch (error) {
      console.error('Place details fetch error:', error.message);
      Alert.alert('Error', 'Network error occurred.');
      return null;
    }
  };

  const decodePolyline = (encoded) => {
    let points = [];
    let index = 0, len = encoded.length;
    let lat = 0, lng = 0;
    while (index < len) {
      let b, shift = 0, result = 0;
      do {
        b = encoded.charCodeAt(index++) - 63;
        result |= (b & 0x1f) << shift;
        shift += 5;
      } while (b >= 0x20);
      let dlat = ((result & 1) ? ~(result >> 1) : (result >> 1));
      lat += dlat;
      shift = 0;
      result = 0;
      do {
        b = encoded.charCodeAt(index++) - 63;
        result |= (b & 0x1f) << shift;
        shift += 5;
      } while (b >= 0x20);
      let dlng = ((result & 1) ? ~(result >> 1) : (result >> 1));
      lng += dlng;
      points.push({ latitude: lat / 1e5, longitude: lng / 1e5 });
    }
    return points;
  };

  const debouncedFetchGates = useCallback(
    debounce(() => {
      fetchGates(routeCoordinates, setGates, setFetchingGates);
    }, 500),
    [routeCoordinates]
  );

  const handlePredictionPress = async (placeId) => {
    if (predictionLoading) return;
    setPredictionLoading(true);
    const details = await fetchPlaceDetails(placeId);
    if (!details?.geometry?.location) {
      console.error('Invalid place data:', details);
      Alert.alert('Error', 'Unable to retrieve location details.');
      setPredictionLoading(false);
      return;
    }
    const { lat, lng } = details.geometry.location;
    const newLocation = {
      latitude: lat,
      longitude: lng,
      latitudeDelta: 0.0922,
      longitudeDelta: 0.0421,
    };
    if (searchMode === 'origin') {
      setOrigin(newLocation);
      setRegion(newLocation);
    } else {
      setDestination(newLocation);
      setRegion(newLocation);
    }
    setSearch('');
    setPredictions([]);
    Keyboard.dismiss();
    setPredictionLoading(false);
  };

  const handleClearSearch = () => {
    setSearch('');
    setPredictions([]);
    Keyboard.dismiss();
  };

  const handleUseCurrentLocation = async () => {
    try {
      const location = await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.High, timeout: 10000 });
      const newLocation = {
        latitude: location.coords.latitude,
        longitude: location.coords.longitude,
        latitudeDelta: 0.0922,
        longitudeDelta: 0.0421,
      };
      console.log('Current location:', newLocation);
      setOrigin(newLocation);
      setRegion(newLocation);
      setSearch('My Current Location');
      setPredictions([]);
    } catch (error) {
      console.error('Current location error:', error);
      Alert.alert('Error', 'Failed to fetch current location.');
    }
  };

  const handleTogglePress = (mode) => {
    setSearchMode(mode);
    setSearch('');
    setPredictions([]);
  };

  const handleGatePress = useCallback(
    debounce((gate) => {
      console.log('Gate pressed:', JSON.stringify(gate, null, 2));
      setSelectedGate(gate);
      sendDataToBackend({ gates, routeCoordinates, selectedGateId: gate.gateNumber, setIsGateLoading, navigation });
    }, 500),
    [gates, routeCoordinates, navigation]
  );

  const resetMap = () => {
    console.log('Resetting map');
    setOrigin(userLocation);
    setDestination(null);
    setRegion(userLocation);
    setRouteCoordinates([]);
    setGates([]);
    setShowGatesButton(false);
    setSearch('');
    setPredictions([]);
    setTripMetadata({ duration: null, distance: null });
    setSelectedGate(null);
  };

  const memoizedGates = useMemo(() => gates, [gates]);
  const memoizedRouteCoordinates = useMemo(() => routeCoordinates, [routeCoordinates]);

  if (!apiKey) {
    console.error('Google Maps API key is missing');
    Alert.alert('Error', 'Google Maps API key is not configured. Please check your .env file.');
    return <View style={styles.container} />;
  }

  if (!userLocation || !region) {
    return (
      <View style={styles.container}>
        <ActivityIndicator style={styles.loading} size="large" color="#00aaff" />
      </View>
    );
  }

  console.log('Rendering MapScreen with SearchComponent and ButtonComponent');

  return (
    <View style={styles.container}>
      <MapComponent
        region={region}
        setRegion={setRegion}
        origin={origin}
        destination={destination}
        routeCoordinates={memoizedRouteCoordinates}
        setRouteCoordinates={setRouteCoordinates}
        gates={memoizedGates}
        mapRef={mapRef}
        handleGatePress={handleGatePress}
        tripMetadata={tripMetadata}
        setTripMetadata={setTripMetadata}
        setShowGatesButton={setShowGatesButton}
      />
      {tripMetadata.duration && tripMetadata.distance && (
        <View style={[styles.metadataContainer, { pointerEvents: 'box-none' }]}>
          <Text style={styles.metadataText}>
            Duration: {(tripMetadata.duration / 60).toFixed(2)} min | Distance: {(tripMetadata.distance / 1000).toFixed(2)} km
          </Text>
        </View>
      )}
      <SearchComponent
        search={search}
        setSearch={setSearch}
        predictions={predictions}
        setPredictions={setPredictions}
        onPredictionPress={handlePredictionPress}
        onClear={handleClearSearch}
        predictionLoading={predictionLoading}
        setPredictionLoading={setPredictionLoading}
        searchMode={searchMode}
        handleTogglePress={handleTogglePress}
      />
      <ButtonComponent
        getCurrentLocation={handleUseCurrentLocation}
        fetchGates={debouncedFetchGates}
        resetMap={resetMap}
        showGatesButton={showGatesButton}
        fetchingGates={fetchingGates}
        sendingData={sendingData}
        isGateLoading={isGateLoading}
        setIsGateLoading={setIsGateLoading}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  loading: {
    position: 'absolute',
    top: '50%',
    left: '50%',
    marginLeft: -18,
    marginTop: -18,
  },
  metadataContainer: {
    position: 'absolute',
    top: 80,
    left: 10,
    backgroundColor: 'rgba(0,0,0,0.7)',
    borderRadius: 5,
    padding: 10,
    zIndex: 5,
  },
  metadataText: {
    color: 'white',
    fontSize: 14,
  },
});

export default MapScreen;