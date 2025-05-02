import { Alert } from 'react-native';
import { Svg, Circle } from 'react-native-svg';
import { View, Text } from 'react-native';

export const LocationButtonIcon = () => (
  <Svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#007AFF" strokeWidth="2">
    <Circle cx="12" cy="12" r="10" strokeLinecap="round" strokeLinejoin="round" />
    <Circle cx="12" cy="12" r="3" fill="#007AFF" />
  </Svg>
);

export const ClusterMarker = ({ count }) => (
  <View style={{ width: 40, height: 40, borderRadius: 20, backgroundColor: 'red', justifyContent: 'center', alignItems: 'center' }}>
    <Text style={{ color: 'white', fontWeight: 'bold', fontSize: 14 }}>{String(count)}</Text>
  </View>
);

export const haversine = (lat1, lon1, lat2, lon2) => {
  const R = 6371;
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
    Math.sin(dLon / 2) * Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
};

export const calculateRouteLength = (coords) => {
  let totalDistance = 0;
  for (let i = 0; i < coords.length - 1; i++) {
    totalDistance += haversine(
      coords[i].latitude,
      coords[i].longitude,
      coords[i + 1].latitude,
      coords[i + 1].longitude
    );
  }
  return totalDistance;
};

export const simplifyCoordinates = (coords) => {
  const routeLength = calculateRouteLength(coords);
  if (routeLength < 50) return coords;
  if (routeLength < 150) return coords.filter((_, index) => index % 5 === 0);
  return coords.filter((_, index) => index % 10 === 0);
};

export const clusterCrossings = (crossings, clusterThreshold = 0.05) => {
  const clusters = [];
  const used = new Set();
  for (let i = 0; i < crossings.length; i++) {
    if (used.has(i)) continue;
    const cluster = [crossings[i]];
    used.add(i);

    for (let j = i + 1; j < crossings.length; j++) {
      if (used.has(j)) continue;
      const dist = haversine(
        crossings[i].latitude,
        crossings[i].longitude,
        crossings[j].latitude,
        crossings[j].longitude
      );
      if (dist < clusterThreshold) {
        cluster.push(crossings[j]);
        used.add(j);
      }
    }

    const avgLat = cluster.reduce((sum, c) => sum + c.latitude, 0) / cluster.length;
    const avgLon = cluster.reduce((sum, c) => sum + c.longitude, 0) / cluster.length;
    clusters.push({
      latitude: avgLat,
      longitude: avgLon,
      crossingCenter: { latitude: avgLat, longitude: avgLon },
      nodeCount: cluster.length,
    });
  }

  return clusters.map((cluster, index) => ({
    ...cluster,
    gateNumber: index + 1,
    name: `Gate ${index + 1}`,
  }));
};

// Utility to delay execution
const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

export const fetchGates = async (routeCoordinates, setGates, setFetchingGates) => {
  if (!routeCoordinates || routeCoordinates.length === 0) {
    Alert.alert("Error", "No route coordinates available.");
    return;
  }
  setFetchingGates(true);

  const bounds = routeCoordinates.reduce(
    (acc, coord) => ({
      minLat: Math.min(acc.minLat, coord.latitude),
      maxLat: Math.max(acc.maxLat, coord.latitude),
      minLon: Math.min(acc.minLon, coord.longitude),
      maxLon: Math.max(acc.maxLon, coord.longitude),
    }),
    { minLat: Infinity, maxLat: -Infinity, minLon: Infinity, maxLon: -Infinity }
  );

  const query = `[out:json][timeout:60];
    node["railway"="level_crossing"](${bounds.minLat - 0.01},${bounds.minLon - 0.01},${bounds.maxLat + 0.01},${bounds.maxLon + 0.01});
    out body;`;

  const endpoints = [
    `https://overpass-api.de/api/interpreter?data=${encodeURIComponent(query)}`,
    `https://z.overpass-api.de/api/interpreter?data=${encodeURIComponent(query)}`,
  ];

  for (let attempt = 1; attempt <= 3; attempt++) {
    for (const url of endpoints) {
      try {
        console.log(`Attempt ${attempt}: Fetching gates from ${url}`);
        const response = await fetch(url, { timeout: 60000 });
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        if (!data.elements || !Array.isArray(data.elements)) {
          throw new Error("Invalid data format from Overpass API");
        }
        if (data.elements.length === 0) {
          Alert.alert("Info", "No railway crossings found in this area.");
          setGates([]);
          setFetchingGates(false); // Ensure state is reset
          return;
        }

        const crossings = data.elements.map(crossing => ({
          latitude: crossing.lat,
          longitude: crossing.lon,
          crossingCenter: { latitude: crossing.lat, longitude: crossing.lon },
        }));

        const simplifiedCrossings = simplifyCoordinates(crossings);
        const clusteredCrossings = clusterCrossings(simplifiedCrossings, 0.05);

        setGates(clusteredCrossings);
        setFetchingGates(false); // Reset state on success
        return; // Success, exit the function
      } catch (error) {
        console.error(`Attempt ${attempt} failed:`, error);
        if (attempt === 3 && url === endpoints[endpoints.length - 1]) {
          // Last attempt and last endpoint
          Alert.alert(
            "Error",
            "Could not fetch railway crossings due to a server timeout. Please check your internet connection and try again."
          );
          setGates([]);
          setFetchingGates(false); // Ensure state is reset
        } else {
          // Wait before retrying
          await delay(2000); // 2-second delay between retries
        }
      }
    }
  }

  setFetchingGates(false); // Ensure state is reset on failure
};

export const sendDataToBackend = async ({ gates, routeCoordinates, selectedGateId, setIsGateLoading, navigation }) => {
  if (selectedGateId) {
    setIsGateLoading(true);
  }
  try {
    const payload = { gates, routeCoordinates, selectedGateId };
    console.log("Sending payload to backend:", JSON.stringify(payload, null, 2));
    const response = await fetch('http://192.168.1.5:5000/railway_data', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`HTTP error! Status: ${response.status}, Body: ${errorText}`);
    }
    const data = await response.json();
    console.log('Backend response:', data);

    if (selectedGateId) {
      const trackedGate = data.gates.find(gate => gate.gate_id === selectedGateId);
      if (trackedGate) {
        console.log('Navigating to GateDetailScreen with gate:', trackedGate);
        navigation.navigate('GateDetailScreen', { gate: trackedGate });
      } else {
        Alert.alert("Error", `Failed to find Gate data with gate_id: ${selectedGateId}`);
      }
    } else {
      setGates(data.gates);
    }
  } catch (error) {
    console.error('Error sending data:', error);
    Alert.alert("Error", `Failed to send railway crossings data: ${error.message}`);
  } finally {
    setIsGateLoading(false);
  }
};