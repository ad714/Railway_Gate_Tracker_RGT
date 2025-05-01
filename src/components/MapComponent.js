import React, { memo, useCallback } from 'react';
import { StyleSheet } from 'react-native';
import MapView, { Marker, Polyline, PROVIDER_GOOGLE } from 'react-native-maps';

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
      console.log('Region changed:', newRegion);
      setRegion(newRegion);
    }, [setRegion]);

    return (
      <MapView
        provider={PROVIDER_GOOGLE}
        style={styles.map}
        region={region}
        onRegionChangeComplete={onRegionChangeComplete}
        showsUserLocation={true}
        ref={mapRef}
      >
        {origin && <Marker coordinate={origin} title="Origin" pinColor="green" key="origin" />}
        {destination && <Marker coordinate={destination} title="Destination" pinColor="red" key="destination" />}
        {routeCoordinates.length > 0 && (
          <Polyline coordinates={routeCoordinates} strokeColor="#00aaff" strokeWidth={4} key="polyline" />
        )}
        {gates.map((gate) => (
          <Marker
            key={`gate-${gate.gateNumber}`}
            coordinate={{ latitude: gate.latitude, longitude: gate.longitude }}
            title={gate.name}
            description={`Gate ID: ${gate.gateNumber}`}
            onPress={() => handleGatePress(gate)}
            pinColor="purple"
          />
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
    zIndex: 1, 
  },
});

export default MapComponent;