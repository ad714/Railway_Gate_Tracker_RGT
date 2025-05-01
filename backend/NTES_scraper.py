import os
import logging
import asyncio
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime, timedelta
import time
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ntes_scraper.log'),
        logging.StreamHandler()
    ]
)

def initialize_browser():
    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--window-size=1200,800")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-webgl")
        options.add_argument("--log-level=3")
        logging.info("Initializing Chrome browser...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        logging.info("Chrome browser initialized successfully.")
        return driver
    except Exception as e:
        logging.error(f"Failed to initialize Chrome browser: {e}")
        return None

def wait_for_element(driver, by, value, description, timeout=10, retries=2):
    attempt = 0
    while attempt < retries:
        try:
            logging.debug(f"Waiting for {description} [Attempt {attempt + 1}/{retries}]")
            element = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            logging.debug(f"{description} found successfully!")
            return element
        except Exception as e:
            logging.warning(f"Failed to find {description}: {e}")
            attempt += 1
            if attempt < retries:
                time.sleep(2)
    logging.error(f"{description} not found after {retries} attempts")
    return None

def extract_time(text):
    """Extract and clean time from a string using regex."""
    try:
        match = re.search(r'\b\d{2}:\d{2}\b', text.strip())
        if match:
            return match.group(0)
        else:
            return None
    except Exception as e:
        logging.error(f"Error extracting time: {e}")
        return None

def extract_train_identifier(text):
    """Extract the train number and route from the train info string."""
    try:
        parts = text.split("|")
        if len(parts) < 2:
            logging.warning(f"Could not split train info: {text}")
            return None, None

        train_no = parts[0].strip()
        match = re.search(r'\b\d{5}\b', train_no)
        if not match:
            logging.warning(f"Could not extract 5-digit train number from: {train_no}")
            return None, None
        train_number = match.group(0)

        name_route = parts[1].strip()
        route_match = re.search(r'\(([^)]+)\)', name_route)
        route = route_match.group(1) if route_match else None

        return train_number, route
    except Exception as e:
        logging.error(f"Error extracting train identifier: {e}")
        return None, None

def is_within_two_hours(time_str, current_time):
    """Check if the given time is within the next 2 hours from the current time."""
    if time_str == "Unknown":
        return False
    try:
        time_clean = extract_time(time_str)
        if not time_clean:
            return False

        now = datetime.combine(datetime.today(), current_time)
        event_time = datetime.strptime(time_clean, "%H:%M")
        event_datetime = datetime.combine(datetime.today(), event_time.time())
        if event_datetime < now:
            event_datetime += timedelta(days=1)

        delta = event_datetime - now
        minutes = delta.total_seconds() // 60
        logging.debug(f"Time {time_clean} vs Now {now.time()}: {minutes} minutes difference")
        return 0 <= minutes <= 120  # 2 hours = 120 minutes
    except Exception as e:
        logging.error(f"Error checking if time is within two hours: {e}")
        return False

async def get_live_trains(driver, station_name):
    try:
        if "mntes" not in driver.current_url:
            logging.info(f"Navigating to NTES main page for {station_name}")
            driver.get("https://enquiry.indianrail.gov.in/mntes/")
            wait_for_element(driver, By.XPATH, "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'live station')]", "Live Station button")

        logging.info(f"Clicking 'Live Station' link for {station_name}")
        live_station_btn = wait_for_element(
            driver,
            By.XPATH,
            "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'live station')]",
            "Live Station button"
        )
        if live_station_btn:
            live_station_btn.click()
            time.sleep(2)
        else:
            logging.info(f"Falling back to direct URL for {station_name}")
            driver.get("https://enquiry.indianrail.gov.in/mntes/liveStation")
            time.sleep(2)

        station_input = wait_for_element(driver, By.ID, "jFromStationInput", "Station input")
        if not station_input:
            raise Exception("Station input field not found")

        logging.info(f"Entering station code: {station_name}")
        station_input.clear()
        station_input.send_keys(station_name)
        WebDriverWait(driver, 2).until(
            lambda d: station_input.get_attribute("value") == station_name
        )

        time_radio = wait_for_element(driver, By.XPATH, "//input[@name='nHr' and @value='2']", "2-hour radio button")
        if not time_radio:
            raise Exception("2-hour radio button not found")
        driver.execute_script("arguments[0].click();", time_radio)

        submit_btn = wait_for_element(driver, By.XPATH, "//input[@value='Get Trains']", "Submit button")
        if not submit_btn:
            raise Exception("Submit button not found")
        logging.info(f"Clicking 'Get Trains' button for {station_name}")
        submit_btn.click()

        table = wait_for_element(driver, By.XPATH, "//table[contains(@class, 'w3-table')]", "Results table", timeout=20)
        if not table:
            logging.info(f"Refreshing page and retrying for {station_name}")
            driver.refresh()
            time.sleep(2)
            submit_btn = wait_for_element(driver, By.XPATH, "//input[@value='Get Trains']", "Submit button")
            if submit_btn:
                submit_btn.click()
            table = wait_for_element(driver, By.XPATH, "//table[contains(@class, 'w3-table')]", "Results table", timeout=20)
            if not table:
                raise Exception("Results table not found after retry")

        trains = []
        rows = table.find_elements(By.XPATH, ".//tbody/tr[position()>1]")
        logging.info(f"Found {len(rows)} trains at {station_name}")

        current_time = datetime.now().time()
        last_updated = datetime.now().isoformat() + "Z"

        for row in rows:
            try:
                cols = row.find_elements(By.TAG_NAME, "td")
                if len(cols) >= 5:
                    train_text = cols[1].text
                    train_no, route = extract_train_identifier(train_text)
                    if not train_no or not route:
                        continue

                    name_match = re.search(r'\|\s*(.*?)\s*\(', train_text)
                    train_name = name_match.group(1).strip() if name_match else ""

                    route_parts = route.split("-")
                    origin = route_parts[0] if route_parts else ""
                    destination = route_parts[1] if len(route_parts) > 1 else ""

                    arrival_time_str = extract_time(cols[2].text.strip()) or "Unknown"
                    departure_time_str = extract_time(cols[3].text.strip()) or "Unknown"

                    if departure_time_str.lower() in ["source", "destination"] or not is_within_two_hours(departure_time_str, current_time):
                        continue

                    train_data = {
                        "trainNumber": train_no,
                        "trainName": train_name,
                        "route": {"origin": origin, "destination": destination, "fullRoute": route},
                        "schedule": {"arrival": arrival_time_str, "departure": departure_time_str},
                        "metadata": {"queriedStation": station_name, "lastUpdated": last_updated},
                        "direction": {"from": "", "to": ""}
                    }
                    trains.append(train_data)
            except Exception as e:
                logging.error(f"Error processing row for {station_name}: {e}")

        logging.info(f"Found {len(trains)} trains within 2 hours at {station_name}")
        for train in trains:
            logging.info(f"Train at {station_name}: {train['trainNumber']} ({train['trainName']}), Arrival: {train['schedule']['arrival']}, Departure: {train['schedule']['departure']}")
        return trains

    except Exception as e:
        logging.error(f"Error scraping {station_name}: {e}")
        return []

def approximate_gate_passage_time(j1_time, j2_time, j1_lat, j1_lon, j2_lat, j2_lon, gate_lat, gate_lon):
    """Approximate when a train passes the gate based on J1 and J2 times and distances."""
    try:
        from math import sqrt
        now = datetime.now()
        j1_dt = datetime.combine(now.date(), datetime.strptime(j1_time, "%H:%M").time())
        j2_dt = datetime.combine(now.date(), datetime.strptime(j2_time, "%H:%M").time())

        if j1_dt < now:
            j1_dt += timedelta(days=1)
        if j2_dt < now:
            j2_dt += timedelta(days=1)

        j1_to_j2_dist = sqrt((j2_lat - j1_lat) ** 2 + (j2_lon - j1_lon) ** 2)
        j1_to_gate_dist = sqrt((gate_lat - j1_lat) ** 2 + (gate_lon - j1_lon) ** 2)
        fraction = j1_to_gate_dist / j1_to_j2_dist if j1_to_j2_dist > 0 else 0

        time_diff = (j2_dt - j1_dt).total_seconds() / 60
        gate_pass_minutes = time_diff * fraction

        gate_pass_dt = j1_dt + timedelta(minutes=gate_pass_minutes)
        return gate_pass_dt.strftime("%H:%M")
    except Exception as e:
        logging.error(f"Error approximating gate passage time: {e}")
        return None

async def fetch_live_train_data(station_data): # Remove default mode, add selected_gate_id
    logging.info("Fetching live train data...")
    driver = initialize_browser()
    selected_gate_id = station_data.get("selected_gate_id")
    gates = station_data.get("gates", [])
    if not driver:
        return [{"gate_id": gate.get("gate_id"), "live_trains": [], "gate_status": "Unknown"} for gate in gates]

    try:
        #1. Collect all unique Junction codes:
        unique_junction_codes = set()
        for gate in gates:
            j1 = gate.get("junctions", {}).get("before", {})
            j2 = gate.get("junctions", {}).get("after", {})
            j1_code = j1.get("code", j1.get("name", ""))
            j2_code = j2.get("code", j2.get("name", ""))
            if j1_code:
                unique_junction_codes.add(j1_code)
            if j2_code:
                unique_junction_codes.add(j2_code)
        logging.info(f"Unique Junction codes {unique_junction_codes}")

        #2. Fetch live train data for all unique junction codes:
        all_junction_trains = {}
        for junction_code in unique_junction_codes:
            logging.info(f"Fetching train data for junction: {junction_code}")
            all_junction_trains[junction_code] = await get_live_trains(driver, junction_code)

        #Prioritize the data if selected Gate ID exist
        if selected_gate_id:
            logging.info(f"Prioritizing the Selected gate: {selected_gate_id}")
            #Find the gate's all informatino and add it to be first item
            selected_gate_info = next((gate for gate in gates if gate['gate_id'] == selected_gate_id), None)

            if selected_gate_info:
                gates.remove(selected_gate_info) # remove from the current location
                gates.insert(0,selected_gate_info) # Insert at 0.


        results = []
        current_time = datetime.now().time()

        for gate in gates:
            j1 = gate.get("junctions", {}).get("before", {})
            j2 = gate.get("junctions", {}).get("after", {})
            j1_code = j1.get("code", j1.get("name", ""))
            j2_code = j2.get("code", j2.get("name", ""))
            j1_name = j1.get("name", "")
            j2_name = j2.get("name", "")
            gate_lat = gate.get("position", {}).get("latitude")
            gate_lon = gate.get("position", {}).get("longitude")
            j1_lat = j1.get("position", {}).get("latitude")
            j1_lon = j1.get("position", {}).get("longitude")
            j2_lat = j2.get("position", {}).get("latitude")
            j2_lon = gate.get("position", {}).get("longitude")
            nearest = gate.get("nearest_station", {})
            adjacent = gate.get("adjacent_stations", {})
            nearest_name = nearest.get("name", "")
            nearest_code = nearest.get("code", "")
            before_name = adjacent.get("before", {}).get("name", "")
            before_code = adjacent.get("before", {}).get("code", "")
            after_name = adjacent.get("after", {}).get("name", "")
            after_code = adjacent.get("after", {}).get("code", "")

            if not (j1_code and j2_code and gate_lat and gate_lon and j1_lat and j1_lon and j2_lat and j2_lon):
                logging.warning(f"Skipping gate {gate.get('gate_id')} due to missing data")
                results.append({"gate_id": gate.get("gate_id"), "live_trains": [], "gate_status": "Unknown"})
                continue

            #3. Retrieve trains from the pre-fetched data:
            j1_trains = all_junction_trains.get(j1_code, [])
            j2_trains = all_junction_trains.get(j2_code, [])


            filtered_trains = []
            for j1_train in j1_trains:
                for j2_train in j2_trains:
                    if j1_train["trainNumber"] == j2_train["trainNumber"]:
                        j1_departure = extract_time(j1_train["schedule"]["departure"])
                        j2_departure = extract_time(j2_train["schedule"]["departure"])
                        if j1_departure and j2_departure:
                            j1_time = datetime.strptime(j1_departure, "%H:%M")
                            j2_time = datetime.strptime(j2_departure, "%H:%M")
                            direction = "J1 to J2" if j1_time < j2_time else "J2 to J1"
                            train_data = j1_train if direction == "J1 to J2" else j2_train
                            train_data["direction"]["from"] = j1_code if direction == "J1 to J2" else j2_code
                            train_data["direction"]["to"] = j2_code if direction == "J1 to J2" else j1_code
                            train_data["schedule"]["arrival_at_J1"] = j1_train["schedule"]["arrival"]
                            train_data["schedule"]["departure_at_J1"] = j1_departure
                            train_data["schedule"]["arrival_at_J2"] = j2_train["schedule"]["arrival"]
                            train_data["schedule"]["departure_at_J2"] = j2_departure

                            gate_pass_time = approximate_gate_passage_time(
                                j1_departure, j2_departure, j1_lat, j1_lon, j2_lat, j2_lon, gate_lat, gate_lon
                            )
                            if gate_pass_time:
                                train_data["schedule"]["gate_passage"] = gate_pass_time
                                logging.info(f"Train {train_data['trainNumber']} gate passage: {gate_pass_time}, Within 2 hours: {is_within_two_hours(gate_pass_time, current_time)}")
                                if is_within_two_hours(gate_pass_time, current_time):
                                    filtered_trains.append(train_data)

            live_trains = sorted(filtered_trains, key=lambda x: datetime.strptime(extract_time(x["schedule"]["gate_passage"]), "%H:%M").time())
            gate_status = "Closed" if live_trains else "Open"

            log_output = f"\nGATE: {gate.get('gate_id')}\n"
            log_output += f"NEAREST STATION: {nearest_name} ({nearest_code})\n"
            log_output += f"ADJACENT STATIONS: {before_name} ({before_code}) - {after_name} ({after_code})\n"
            log_output += f"JUNCTION STATIONS: {j1_name} ({j1_code}) - {j2_name} ({j2_code})\n"
            log_output += "TRAINS PASSING WITH TIME:\n"
            if live_trains:
                for train in live_trains:
                    log_output += f"- {train['trainNumber']} ({train['trainName']}): J1 {train['schedule']['arrival_at_J1']}/{train['schedule']['departure_at_J1']} -> J2 {train['schedule']['arrival_at_J2']}/{train['schedule']['departure_at_J2']}, Gate Passage: {train['schedule']['gate_passage']}\n"
            else:
                log_output += "- None\n"
            log_output += f"GATE STATUS: {gate_status}"
            logging.info(log_output)

            results.append({
                "gate_id": gate.get("gate_id"),
                "live_trains": live_trains,
                "gate_status": gate_status
            })

        return results

    except Exception as e:
        logging.error(f"Error in fetch_live_train_data: {e}")
        return [{"gate_id": gate.get("gate_id"), "live_trains": [], "gate_status": "Unknown"} for gate in gates]

    finally:
        logging.info("Closing browser...")
        if driver:
            driver.quit()