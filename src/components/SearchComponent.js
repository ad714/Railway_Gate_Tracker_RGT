import React from 'react';
import { View, TouchableOpacity, FlatList, ActivityIndicator, Text } from 'react-native';
import { SearchBar } from '@rneui/themed';
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
}) => {
  const apiKey = Constants.expoConfig?.extra?.expoPublicGoogleMapsApiKey;

  const updateSearch = async (text) => {
    setSearch(text);
    if (text.length < 2) {
      setPredictions([]);
      setPredictionLoading(false);
      return;
    }
    setPredictionLoading(true);
    try {
      const response = await fetch(
        `https://maps.googleapis.com/maps/api/place/autocomplete/json?input=${encodeURIComponent(text)}&key=${apiKey}&language=en`
      );
      const data = await response.json();
      console.log('Search API Response:', JSON.stringify(data, null, 2));
      if (data.status === 'OK') {
        setPredictions(data.predictions || []);
      } else if (data.status === 'ZERO_RESULTS') {
        console.log('No results for query:', text);
        setPredictions([]);
      } else {
        console.error('Search API error:', data.status, data.error_message || 'Unknown error');
        setPredictions([]);
      }
    } catch (error) {
      console.error('Search error:', error.message);
      setPredictions([]);
    } finally {
      setPredictionLoading(false);
    }
  };

  const renderItem = ({ item }) => (
    <TouchableOpacity style={styles.predictionItem} onPress={() => onPredictionPress(item.place_id)}>
      <Text style={styles.predictionText}>{item.description || 'No description available'}</Text>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <SearchBar
        placeholder="Search for places, shops, or addresses"
        value={search}
        onChangeText={updateSearch}
        onClear={onClear}
        inputStyle={styles.searchInput}
        containerStyle={styles.searchContainer}
        inputContainerStyle={styles.searchInputContainer}
        placeholderTextColor="#888"
        searchIcon={{ type: 'ionicon', name: 'search', color: 'black' }}
        clearIcon={{ type: 'ionicon', name: 'close-circle', color: 'black' }}
      />
      {predictions.length > 0 && (
        <View style={styles.predictionsContainer}>
          <FlatList
            data={predictions}
            renderItem={renderItem}
            keyExtractor={(item) => item.place_id}
            keyboardShouldPersistTaps="always"
          />
        </View>
      )}
      {predictionLoading && <ActivityIndicator size="small" color="#0000ff" style={styles.loader} />}
    </View>
  );
};

const styles = {
  container: {
    position: 'absolute',
    top: 40,
    width: '100%',
    paddingHorizontal: 15,
    zIndex: 1,
  },
  searchContainer: {
    backgroundColor: 'transparent',
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 0,
  },
  searchInputContainer: {
    backgroundColor: 'white',
    borderRadius: 5,
    borderWidth: 0,
  },
  searchInput: {
    backgroundColor: 'white',
    color: 'black',
    padding: 10,
    fontSize: 16,
  },
  predictionsContainer: {
    backgroundColor: 'white',
    maxHeight: 200,
    marginTop: 5,
    borderRadius: 5,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
  },
  predictionItem: {
    padding: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#ddd',
  },
  predictionText: {
    fontSize: 16,
    color: 'black',
  },
  loader: {
    marginTop: 5,
  },
};

export default SearchComponent;