import React from 'react';
import { View, StyleSheet } from 'react-native';
import { Button } from '@rneui/themed';
import { Ionicons } from '@expo/vector-icons';

const ButtonComponent = ({
  getCurrentLocation,
  fetchGates,
  resetMap,
  showGatesButton,
  fetchingGates,
  sendingData,
  isGateLoading,
  setIsGateLoading,
}) => {
  return (
    <View style={styles.container}>
      <Button
        icon={<Ionicons name="location" size={24} color="white" />}
        onPress={getCurrentLocation}
        containerStyle={styles.floatingButton}
        buttonStyle={styles.floatingButtonStyle}
      />
      <View style={styles.bottomRow}>
        {showGatesButton && (
          <Button
            title={fetchingGates ? 'Loading...' : sendingData ? 'Sending...' : 'Show Gates'}
            onPress={fetchGates}
            disabled={fetchingGates || sendingData}
            containerStyle={styles.button}
            buttonStyle={styles.buttonStyle}
            titleStyle={styles.buttonText}
            loading={fetchingGates || sendingData}
          />
        )}
        <Button
          title="Reset Map"
          onPress={resetMap}
          containerStyle={styles.button}
          buttonStyle={styles.buttonStyle}
          titleStyle={styles.buttonText}
        />
      </View>
      {isGateLoading && (
        <View style={styles.loadingOverlay}>
          <Button
            loading
            title="Fetching Gate Details..."
            disabled
            containerStyle={styles.loadingButton}
            buttonStyle={styles.loadingButtonStyle}
            titleStyle={styles.loadingButtonText}
          />
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    zIndex: 8, // Lower than SearchComponent
  },
  floatingButton: {
    position: 'absolute',
    right: 20,
    top: 120,
    borderRadius: 25,
  },
  floatingButtonStyle: {
    backgroundColor: '#00aaff',
    borderRadius: 25,
    width: 50,
    height: 50,
    justifyContent: 'center',
    alignItems: 'center',
  },
  bottomRow: {
    position: 'absolute',
    bottom: 20,
    left: 20,
    right: 20,
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  button: {
    flex: 1,
    marginHorizontal: 5,
  },
  buttonStyle: {
    backgroundColor: '#00aaff',
    borderRadius: 5,
    paddingVertical: 10,
  },
  buttonText: {
    color: 'white',
    fontSize: 14,
    textAlign: 'center',
  },
  loadingOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 9, // Higher than container but lower than SearchComponent
  },
  loadingButton: {
    width: '80%',
  },
  loadingButtonStyle: {
    backgroundColor: '#333',
    borderRadius: 5,
    paddingVertical: 10,
  },
  loadingButtonText: {
    color: 'white',
    fontSize: 16,
    marginLeft: 10,
  },
});

export default ButtonComponent;