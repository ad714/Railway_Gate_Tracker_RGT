import React, { useState, useEffect } from 'react';
import { View, StyleSheet, ActivityIndicator, Alert, Keyboard } from 'react-native';
import MapView, { Marker, PROVIDER_GOOGLE } from 'react-native-maps';
import * as Location from 'expo-location';
import Constants from 'expo-constants';
import SearchComponent from '../components/SearchComponent';

const MapScreen = () => {
  const apiKey = Constants.expoConfig?.extra?.expoPublicGoogleMapsApiKey;
  const [userLocation, setUserLocation] = useState(null);
  const [region, setRegion] = useState(null);
  const [search, setSearch] = useState('');
  const [predictions, setPredictions] = useState([]);
  const [predictionLoading, setPredictionLoading] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const { status } = await Location.requestForegroundPermissionsAsync();
        if (status !== 'granted') {
          Alert.alert('Location Permission Denied', 'Please enable location services.');
          return;
        }
        const location = await Location.getCurrentPositionAsync({ timeout: 10000 });
        setUserLocation(location.coords);
        setRegion({
          latitude: location.coords.latitude,
          longitude: location.coords.longitude,
          latitudeDelta: 0.0922,
          longitudeDelta: 0.0421,
        });
      } catch (error) {
        console.error('Location error:', error);
        Alert.alert('Error', 'Failed to fetch location.');
      }
    })();
  }, []);

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

  const handlePredictionPress = async (placeId) => {
    const details = await fetchPlaceDetails(placeId);
    if (!details?.geometry?.location) {
      console.error('Invalid place data:', details);
      Alert.alert('Error', 'Unable to retrieve location details.');
      return;
    }
    const { lat, lng } = details.geometry.location;
    setRegion({
      latitude: lat,
      longitude: lng,
      latitudeDelta: 0.0922,
      longitudeDelta: 0.0421,
    });
    setUserLocation({
      latitude: lat,
      longitude: lng,
    });
    setSearch('');
    setPredictions([]);
    Keyboard.dismiss();
  };

  const handleClearSearch = () => {
    setSearch('');
    setPredictions([]);
    if (userLocation) {
      setRegion({
        latitude: userLocation.latitude,
        longitude: userLocation.longitude,
        latitudeDelta: 0.0922,
        longitudeDelta: 0.0421,
      });
    }
    Keyboard.dismiss();
  };

  if (!apiKey) {
    console.error('Google Maps API key is missing');
    Alert.alert('Error', 'Google Maps API key is not configured. Please check your .env file.');
    return <View style={styles.container} />;
  }

  return (
    <View style={styles.container}>
      <SearchComponent
        search={search}
        setSearch={setSearch}
        predictions={predictions}
        setPredictions={setPredictions}
        onPredictionPress={handlePredictionPress}
        onClear={handleClearSearch}
        predictionLoading={predictionLoading}
        setPredictionLoading={setPredictionLoading}
      />
      {region && userLocation && (
        <MapView
          provider={PROVIDER_GOOGLE}
          style={styles.map}
          region={region}
          showsUserLocation={true}
          onRegionChangeComplete={(newRegion) => setRegion(newRegion)}
        >
          <Marker coordinate={userLocation} />
        </MapView>
      )}
      {!userLocation && (
        <ActivityIndicator style={styles.loading} size="large" color="blue" />
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  map: {
    width: '100%',
    height: '100%',
  },
  loading: {
    position: 'absolute',
    top: '50%',
    left: '50%',
    marginLeft: -18,
    marginTop: -18,
  },
});

export default MapScreen;