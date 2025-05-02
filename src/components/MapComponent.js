import React, { memo, useCallback, useEffect } from 'react';
import { StyleSheet, View } from 'react-native';
import MapView, { Marker, Polyline, PROVIDER_GOOGLE } from 'react-native-maps';
import { ClusterMarker } from '../utils'; // Import ClusterMarker

const MapComponent = memo(
  ({
    region,
    setRegion,
    origin,
    destination,
    routeCoordinates,
    setRouteCoordinates,
    gates,
    mapRef,
    handleGatePress,
    tripMetadata,
    setTripMetadata,
    setShowGatesButton,
  }) => {
    const onRegionChangeComplete = useCallback((newRegion) => {
      // Only update region if it's the initial setup or a significant change
      const deltaChange = Math.abs(newRegion.latitudeDelta - region.latitudeDelta) > 0.01 ||
                         Math.abs(newRegion.longitudeDelta - region.latitudeDelta) > 0.01;
      if (deltaChange) {
        setRegion(newRegion);
      }
    }, [setRegion, region]);

    // Debug gesture events
    const onPanDrag = useCallback(() => {
      console.log('Map is being panned');
    }, []);

    useEffect(() => {
      console.log('MapComponent mounted');
    }, []);

    return (
      <MapView
        provider={PROVIDER_GOOGLE}
        style={styles.map}
        region={region}
        onRegionChangeComplete={onRegionChangeComplete}
        onPanDrag={onPanDrag} // Debug panning
        showsUserLocation={false}
        ref={mapRef}
        scrollEnabled={true} // Enable panning
        zoomEnabled={true}   // Enable zooming
        rotateEnabled={true} // Enable rotation
        pitchEnabled={true}  // Enable tilt
      >
        {origin && <Marker coordinate={origin} title="Origin" pinColor="green" key="origin" />}
        {destination && <Marker coordinate={destination} title="Destination" pinColor="red" key="destination" />}
        {routeCoordinates.length > 0 && (
          <Polyline coordinates={routeCoordinates} strokeColor="#00aaff" strokeWidth={4} key="polyline" />
        )}
        {gates.map((gate) => (
          gate.nodeCount > 1 ? (
            <Marker
              key={`gate-${gate.gateNumber}`}
              coordinate={{ latitude: gate.latitude, longitude: gate.longitude }}
              onPress={() => handleGatePress(gate)}
            >
              <ClusterMarker count={gate.nodeCount} />
            </Marker>
          ) : (
            <Marker
              key={`gate-${gate.gateNumber}`}
              coordinate={{ latitude: gate.latitude, longitude: gate.longitude }}
              title={gate.name}
              description={`Gate ID: ${gate.gateNumber}`}
              onPress={() => handleGatePress(gate)}
              pinColor="orange"
            />
          )
        ))}
      </MapView>
    );
  },
  (prevProps, nextProps) => {
    return (
      prevProps.region === nextProps.region &&
      prevProps.origin === nextProps.origin &&
      prevProps.destination === nextProps.destination &&
      prevProps.routeCoordinates === nextProps.routeCoordinates &&
      prevProps.gates === nextProps.gates &&
      prevProps.tripMetadata === nextProps.tripMetadata
    );
  }
);

const styles = StyleSheet.create({
  map: {
    width: '100%',
    height: '100%',
    zIndex: 1, // Set back to 1
  },
});

export default MapComponent;