import React, { useEffect } from 'react';
import { View, TextInput, FlatList, Text, TouchableOpacity, StyleSheet } from 'react-native';
import Constants from 'expo-constants';

const SearchComponent = ({
  search,
  setSearch,
  predictions,
  setPredictions,
  onPredictionPress,
  onClear,
  predictionLoading,
  setPredictionLoading,
  searchMode,
  handleTogglePress,
}) => {
  const apiKey = Constants.expoConfig?.extra?.expoPublicGoogleMapsApiKey;

  useEffect(() => {
    console.log('SearchComponent mounted');
  }, []);

  const fetchPredictions = async (input) => {
    if (!input) {
      setPredictions([]);
      return;
    }
    setPredictionLoading(true);
    try {
      const response = await fetch(
        `https://maps.googleapis.com/maps/api/place/autocomplete/json?input=${encodeURIComponent(input)}&key=${apiKey}`
      );
      const data = await response.json();
      if (data.status === 'OK') {
        setPredictions(data.predictions);
      } else {
        setPredictions([]);
      }
    } catch (error) {
      console.error('Prediction fetch error:', error);
    } finally {
      setPredictionLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.toggleContainer}>
        <TouchableOpacity
          style={[styles.toggleButton, searchMode === 'origin' ? styles.activeToggle : null]}
          onPress={() => {
            console.log('Origin toggle pressed');
            handleTogglePress('origin');
          }}
        >
          <Text style={[styles.toggleText, searchMode === 'origin' ? styles.activeToggleText : null]}>
            Origin
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.toggleButton, searchMode === 'destination' ? styles.activeToggle : null]}
          onPress={() => {
            console.log('Destination toggle pressed');
            handleTogglePress('destination');
          }}
        >
          <Text style={[styles.toggleText, searchMode === 'destination' ? styles.activeToggleText : null]}>
            Destination
          </Text>
        </TouchableOpacity>
      </View>
      <TextInput
        style={styles.input}
        value={search}
        onChangeText={(text) => {
          setSearch(text);
          fetchPredictions(text);
        }}
        placeholder={`Search for ${searchMode.charAt(0).toUpperCase() + searchMode.slice(1)}`}
        onSubmitEditing={onClear}
      />
      {predictionLoading && <Text style={styles.loadingText}>Loading...</Text>}
      <FlatList
        data={predictions}
        keyExtractor={(item) => item.place_id}
        renderItem={({ item }) => (
          <TouchableOpacity
            onPress={() => {
              console.log('Prediction pressed:', item.place_id);
              onPredictionPress(item.place_id);
            }}
            style={styles.predictionItem}
          >
            <Text style={styles.prediction}>{item.description}</Text>
          </TouchableOpacity>
        )}
        style={styles.predictionList}
        pointerEvents="auto"
      />
      {search && (
        <TouchableOpacity onPress={onClear} style={styles.clearButton}>
          <Text style={styles.clearButtonText}>Clear</Text>
        </TouchableOpacity>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    top: 10,
    left: 10,
    right: 10,
    backgroundColor: 'white',
    borderRadius: 5,
    padding: 10,
    zIndex: 10, // Lowered zIndex
    opacity: 1,
  },
  toggleContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 10,
  },
  toggleButton: {
    flex: 1,
    paddingVertical: 8,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 5,
    marginHorizontal: 5,
  },
  activeToggle: {
    backgroundColor: '#00aaff',
    borderColor: '#00aaff',
  },
  toggleText: {
    color: '#333',
    fontSize: 14,
  },
  activeToggleText: {
    color: 'white',
  },
  input: {
    height: 40,
    borderColor: 'gray',
    borderWidth: 1,
    borderRadius: 5,
    paddingHorizontal: 10,
  },
  loadingText: {
    color: '#00aaff',
    textAlign: 'center',
    marginTop: 5,
  },
  predictionList: {
    maxHeight: 200,
  },
  predictionItem: {
    padding: 10,
  },
  prediction: {
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  clearButton: {
    position: 'absolute',
    right: 20,
    top: 60,
    backgroundColor: '#ddd',
    padding: 5,
    borderRadius: 5,
    zIndex: 11,
    opacity: 1,
  },
  clearButtonText: {
    color: '#333',
    fontSize: 12,
  },
});

export default SearchComponent;