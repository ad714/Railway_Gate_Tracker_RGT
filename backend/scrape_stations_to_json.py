import json
import logging
import os
from dotenv import load_dotenv
import googlemaps
import time

logging.basicConfig(level=logging.DEBUG)
load_dotenv()

#  station data with routes (THIS IS NOW THE PRIMARY DATA SOURCE)
stations_data = [
    {"station_name": "Parassala", "station_code": "PASA", "route": "Trivandrum to Kollam", "lat": None, "lon": None},
    {"station_name": "Dhanuvachapuram (halt)", "station_code": "DAVM", "route": "Trivandrum to Kollam", "lat": None, "lon": None},
    {"station_name": "Amaravila (halt)", "station_code": "AMVA", "route": "Trivandrum to Kollam", "lat": None, "lon": None},
    {"station_name": "Neyyattinkara", "station_code": "NYY", "route": "Trivandrum to Kollam", "lat": None, "lon": None},
    {"station_name": "Balaramapuram", "station_code": "BRAM", "route": "Trivandrum to Kollam", "lat": None, "lon": None},
    {"station_name": "Nemom", "station_code": "NEM", "route": "Trivandrum to Kollam", "lat": None, "lon": None},
    {"station_name": "Thiruvananthapuram Central", "station_code": "TVC", "route": "Trivandrum to Kollam", "lat": None, "lon": None},
    {"station_name": "Thiruvananthapuram pettah", "station_code": "TVP", "route": "Trivandrum to Kollam", "lat": None, "lon": None},
    {"station_name": "Kochuveli", "station_code": "KCVL", "route": "Trivandrum to Kollam", "lat": None, "lon": None},
    {"station_name": "Veli (halt)", "station_code": "VELI", "route": "Trivandrum to Kollam", "lat": None, "lon": None},
    {"station_name": "Kazhakuttam", "station_code": "KZK", "route": "Trivandrum to Kollam", "lat": None, "lon": None},
    {"station_name": "Kaniyapuram", "station_code": "KXP", "route": "Trivandrum to Kollam", "lat": None, "lon": None},
    {"station_name": "Murukkampuzha", "station_code": "MQU", "route": "Trivandrum to Kollam", "lat": None, "lon": None},
    {"station_name": "Perunguzhi (halt)", "station_code": "PGZ", "route": "Trivandrum to Kollam", "lat": None, "lon": None},
    {"station_name": "Chirayinkeezh", "station_code": "CRY", "route": "Trivandrum to Kollam", "lat": None, "lon": None},
    {"station_name": "Kadakavur", "station_code": "KVU", "route": "Trivandrum to Kollam", "lat": None, "lon": None},
    {"station_name": "Akathumuri (halt)", "station_code": "AMY", "route": "Trivandrum to Kollam", "lat": None, "lon": None},
    {"station_name": "Varkala Shivagiri", "station_code": "VAK", "route": "Trivandrum to Kollam", "lat": None, "lon": None},
    {"station_name": "Edavai", "station_code": "EVA", "route": "Trivandrum to Kollam", "lat": None, "lon": None},
    {"station_name": "Kappil", "station_code": "KFI", "route": "Trivandrum to Kollam", "lat": None, "lon": None},
    {"station_name": "Paravur", "station_code": "PVU", "route": "Trivandrum to Kollam", "lat": None, "lon": None},
    {"station_name": "Mayyanad", "station_code": "MYY", "route": "Trivandrum to Kollam", "lat": None, "lon": None},
    {"station_name": "Iravipuram (halt)", "station_code": "IRP", "route": "Trivandrum to Kollam", "lat": None, "lon": None},
    {"station_name": "Kollam Jn", "station_code": "QLN", "route": "Kollam to Kayamkulam"},
    {"station_name": "Perinad (halt)", "station_code": "PRND", "route": "Kollam to Kayamkulam", "lat": None, "lon": None},
    {"station_name": "Munroturuttu (halt)", "station_code": "MQO", "route": "Kollam to Kayamkulam", "lat": None, "lon": None},
    {"station_name": "Sasthankotta", "station_code": "STKT", "route": "Kollam to Kayamkulam", "lat": None, "lon": None},
    {"station_name": "Karunagapalli", "station_code": "KPY", "route": "Kollam to Kayamkulam", "lat": None, "lon": None},
    {"station_name": "Ochira", "station_code": "OCR", "route": "Kollam to Kayamkulam", "lat": None, "lon": None},
    {"station_name": "Kayankulam Jn", "station_code": "KYJ", "route": "Kayamkulam via Alleppey to Ernakulam"},
    {"station_name": "Cheppad (halt)", "station_code": "CHPD", "route": "Kayamkulam - Eranakulam via Alappuzha", "lat": None, "lon": None},
    {"station_name": "Harippad", "station_code": "HAD", "route": "Kayamkulam - Eranakulam via Alappuzha", "lat": None, "lon": None},
    {"station_name": "Karuvatta (halt)", "station_code": "KVTA", "route": "Kayamkulam - Eranakulam via Alappuzha", "lat": None, "lon": None},
    {"station_name": "Takazhi (halt)", "station_code": "TZH", "route": "Kayamkulam - Eranakulam via Alappuzha", "lat": None, "lon": None},
    {"station_name": "Ambalapuzha", "station_code": "AMPA", "route": "Kayamkulam - Eranakulam via Alappuzha", "lat": None, "lon": None},
    {"station_name": "Punnapra (halt)", "station_code": "PNPR", "route": "Kayamkulam - Eranakulam via Alappuzha", "lat": None, "lon": None},
    {"station_name": "Alappuzha", "station_code": "ALLP", "route": "Kayamkulam - Eranakulam via Alappuzha"},
    {"station_name": "Tumboli (halt)", "station_code": "TMPY", "route": "Kayamkulam - Eranakulam via Alappuzha", "lat": None, "lon": None},
    {"station_name": "Kalavur (halt)", "station_code": "KAVR", "route": "Kayamkulam - Eranakulam via Alappuzha", "lat": None, "lon": None},
    {"station_name": "Mararikulam", "station_code": "MAKM", "route": "Kayamkulam - Eranakulam via Alappuzha", "lat": None, "lon": None},
    {"station_name": "Tiruvizha (halt)", "station_code": "TRVZ", "route": "Kayamkulam - Ernakulam via Alappuzha", "lat": None, "lon": None},
    {"station_name": "Cherthala", "station_code": "SRTL", "route": "Kayamkulam - Ernakulam via Alappuzha", "lat": None, "lon": None},
    {"station_name": "Vayalar (halt)", "station_code": "VAY", "route": "Kayamkulam - Ernakulam via Alappuzha", "lat": None, "lon": None},
    {"station_name": "Turavur", "station_code": "TUVR", "route": "Kayamkulam - Ernakulam via Alappuzha", "lat": None, "lon": None},
    {"station_name": "Ezhupunna (halt)", "station_code": "EZP", "route": "Kayamkulam - Ernakulam via Alappuzha", "lat": None, "lon": None},
    {"station_name": "Aroor (halt)", "station_code": "AROR", "route": "Kayamkulam - Ernakulam via Alappuzha", "lat": None, "lon": None},
    {"station_name": "Kumblam", "station_code": "KUMM", "route": "Kayamkulam - Ernakulam via Alappuzha", "lat": None, "lon": None},
    {"station_name": "Tirunettur (halt)", "station_code": "TNU", "route": "Kayamkulam - Ernakulam via Alappuzha", "lat": None, "lon": None},
    {"station_name": "Mavelikara", "station_code": "MVLK", "route": "Kayamkulam via Kottayam to Ernakulam", "lat": None, "lon": None},
    {"station_name": "Cheriyanad", "station_code": "CYN", "route": "Kayamkulam via Kottayam to Ernakulam", "lat": None, "lon": None},
    {"station_name": "Chengannur", "station_code": "CNGR", "route": "Kayamkulam via Kottayam to Ernakulam", "lat": None, "lon": None},
    {"station_name": "Tiruvalla", "station_code": "TRVL", "route": "Kayamkulam via Kottayam to Ernakulam", "lat": None, "lon": None},
    {"station_name": "Changanaseri", "station_code": "CGY", "route": "Kayamkulam via Kottayam to Ernakulam", "lat": None, "lon": None},
    {"station_name": "Chingavanam", "station_code": "CGV", "route": "Kayamkulam via Kottayam to Ernakulam", "lat": None, "lon": None},
    {"station_name": "Kottayam", "station_code": "KTYM", "route": "Kayamkulam via Kottayam to Ernakulam"},
    {"station_name": "Kumaranallur (halt)", "station_code": "KFQ", "route": "Kayamkulam via Kottayam to Ernakulam", "lat": None, "lon": None},
    {"station_name": "Ettumanur", "station_code": "ETM", "route": "Kayamkulam via Kottayam to Ernakulam", "lat": None, "lon": None},
    {"station_name": "Kuruppantara", "station_code": "KRPP", "route": "Kayamkulam via Kottayam to Ernakulam", "lat": None, "lon": None},
    {"station_name": "Kaduturutty (halt)", "station_code": "KDTY", "route": "Kayamkulam via Kottayam to Ernakulam", "lat": None, "lon": None},
    {"station_name": "Vaikom Road", "station_code": "VARD", "route": "Kayamkulam via Kottayam to Ernakulam", "lat": None, "lon": None},
    {"station_name": "Piravam Road", "station_code": "PVRD", "route": "Kayamkulam via Kottayam to Ernakulam", "lat": None, "lon": None},
    {"station_name": "Kanjiramittam(halt)", "station_code": "KPTM", "route": "Kayamkulam via Kottayam to Ernakulam", "lat": None, "lon": None},
    {"station_name": "Mulanturutti", "station_code": "MNTT", "route": "Kayamkulam via Kottayam to Ernakulam", "lat": None, "lon": None},
    {"station_name": "Chottanikkara Road (halt)", "station_code": "KFE", "route": "Kayamkulam via Kottayam to Ernakulam", "lat": None, "lon": None},
    {"station_name": "Tripunitura", "station_code": "TRTR", "route": "Kayamkulam via Kottayam to Ernakulam", "lat": None, "lon": None},
    {"station_name": "Ernakulam Jn", "station_code": "ERS", "route": "Ernakulam to Thrissur"},
    {"station_name": "Ernakulam Town", "station_code": "ERN", "route": "Ernakulam to Thrissur", "lat": None, "lon": None},
    {"station_name": "Idappalli", "station_code": "IPL", "route": "Ernakulam to Thrissur", "lat": None, "lon": None},
    {"station_name": "Kalamasseri", "station_code": "KLMR", "route": "Ernakulam to Thrissur", "lat": None, "lon": None},
    {"station_name": "Aluva", "station_code": "AWY", "route": "Ernakulam to Thrissur", "lat": None, "lon": None},
    {"station_name": "Chovvara (halt)", "station_code": "CWR", "route": "Ernakulam to Thrissur", "lat": None, "lon": None},
    {"station_name": "Angamali (for Kaladi)", "station_code": "AFK", "route": "Ernakulam to Thrissur", "lat": None, "lon": None},
    {"station_name": "Karukutty", "station_code": "KUC", "route": "Ernakulam to Thrissur", "lat": None, "lon": None},
    {"station_name": "Koratti Angadi (halt)", "station_code": "KRAN", "route": "Ernakulam to Thrissur", "lat": None, "lon": None},
    {"station_name": "Divine Nagar (halt)", "station_code": "DINR", "route": "Ernakulam to Thrissur", "lat": None, "lon": None},
    {"station_name": "Chalakudi", "station_code": "CKI", "route": "Ernakulam to Thrissur", "lat": None, "lon": None},
    {"station_name": "Irinjalakuda", "station_code": "IJK", "route": "Ernakulam to Thrissur", "lat": None, "lon": None},
    {"station_name": "Nellayi (halt)", "station_code": "NYI", "route": "Ernakulam to Thrissur", "lat": None, "lon": None},
    {"station_name": "Pudukad", "station_code": "PUK", "route": "Ernakulam to Thrissur", "lat": None, "lon": None},
    {"station_name": "Ollur", "station_code": "OLR", "route": "Ernakulam to Thrissur", "lat": None, "lon": None},
    {"station_name": "Thrisur", "station_code": "TCR", "route": "Thrissur to Shoranur"},
    {"station_name": "Punkunnam", "station_code": "PNQ", "route": "Thrissur to Shoranur", "lat": None, "lon": None},
    {"station_name": "Mulagunnathukavu", "station_code": "MGK", "route": "Thrissur to Shoranur", "lat": None, "lon": None},
    {"station_name": "Wadakancheri", "station_code": "WKI", "route": "Thrissur to Shoranur", "lat": None, "lon": None},
    {"station_name": "Mullurkara (halt)", "station_code": "MUC", "route": "Thrissur to Shoranur", "lat": None, "lon": None},
    {"station_name": "Vallattol Nagar", "station_code": "VTK", "route": "Thrissur to Shoranur", "lat": None, "lon": None},
    {"station_name": "Shoranur Jn.", "station_code": "SRR", "route": "Shoranur to Kozhikode"},
    {"station_name": "Karakkad", "station_code": "KRKD", "route": "Shoranur to Kozhikode", "lat": None, "lon": None},
    {"station_name": "Pattambi", "station_code": "PTB", "route": "Shoranur to Kozhikode", "lat": None, "lon": None},
    {"station_name": "Pallippuram", "station_code": "PUM", "route": "Shoranur to Kozhikode", "lat": None, "lon": None},
    {"station_name": "Kuttippuram", "station_code": "KTU", "route": "Shoranur to Kozhikode", "lat": None, "lon": None},
    {"station_name": "Tirunnavaya", "station_code": "TUA", "route": "Shoranur to Kozhikode", "lat": None, "lon": None},
    {"station_name": "Tirur", "station_code": "TIR", "route": "Shoranur to Kozhikode", "lat": None, "lon": None},
    {"station_name": "Tanur", "station_code": "TA", "route": "Shoranur to Kozhikode", "lat": None, "lon": None},
    {"station_name": "Parappanangadi", "station_code": "PGI", "route": "Shoranur to Kozhikode", "lat": None, "lon": None},
    {"station_name": "Vallikunnu", "station_code": "VLI", "route": "Shoranur to Kozhikode", "lat": None, "lon": None},
    {"station_name": "Kadalundi", "station_code": "KN", "route": "Shoranur to Kozhikode", "lat": None, "lon": None},
    {"station_name": "Ferok", "station_code": "FK", "route": "Shoranur to Kozhikode", "lat": None, "lon": None},
    {"station_name": "Kallayi", "station_code": "KUL", "route": "Shoranur to Kozhikode", "lat": None, "lon": None},
    {"station_name": "Kozhikkode", "station_code": "CLT", "route": "Kozhikode to MAnjeshwar(Kasargode)"},
    {"station_name": "West Hill", "station_code": "WH", "route": "Kozhikode to MAnjeshwar(Kasargode)", "lat": None, "lon": None},
    {"station_name": "Elattur", "station_code": "ETR", "route": "Kozhikode to MAnjeshwar(Kasargode)", "lat": None, "lon": None},
    {"station_name": "Quilandi", "station_code": "QLD", "route": "Kozhikode to MAnjeshwar(Kasargode)", "lat": None, "lon": None},
    {"station_name": "Tikkotti", "station_code": "TKT", "route": "Kozhikode to MAnjeshwar(Kasargode)", "lat": None, "lon": None},
    {"station_name": "Payyoli", "station_code": "PYOL", "route": "Kozhikode to MAnjeshwar(Kasargode)", "lat": None, "lon": None},
    {"station_name": "Iringal", "station_code": "IGL", "route": "Kozhikode to MAnjeshwar(Kasargode)", "lat": None, "lon": None},
    {"station_name": "Vadakara", "station_code": "BDJ", "route": "Kozhikode to MAnjeshwar(Kasargode)", "lat": None, "lon": None},
    {"station_name": "Nadapuram Road", "station_code": "NAU", "route": "Kozhikode to MAnjeshwar(Kasargode)", "lat": None, "lon": None},
    {"station_name": "Mukkali", "station_code": "MUKE", "route": "Kozhikode to MAnjeshwar(Kasargode)", "lat": None, "lon": None},
    {"station_name": "Mahe", "station_code": "MAHE", "route": "Kozhikode to MAnjeshwar(Kasargode)", "lat": None, "lon": None},
    {"station_name": "Jagannath Temple Gate", "station_code": "JGE", "route": "Kozhikode to MAnjeshwar(Kasargode)", "lat": None, "lon": None},
    {"station_name": "Thalassery", "station_code": "TLY", "route": "Kozhikode to MAnjeshwar(Kasargode)", "lat": None, "lon": None},
    {"station_name": "Dharmadam", "station_code": "DMD", "route": "Kozhikode to MAnjeshwar(Kasargode)", "lat": None, "lon": None},
    {"station_name": "Etakkot", "station_code": "ETK", "route": "Kozhikode to MAnjeshwar(Kasargode)", "lat": None, "lon": None},
    {"station_name": "Kannur South", "station_code": "CS", "route": "Kozhikode to MAnjeshwar(Kasargode)", "lat": None, "lon": None},
    {"station_name": "Kannur", "station_code": "CAN", "route": "Kannur to Kasaragod"},
    {"station_name": "Chirakkal", "station_code": "CQL", "route": "Kozhikode to MAnjeshwar(Kasargode)", "lat": None, "lon": None},
    {"station_name": "Valapattanam", "station_code": "VAPM", "route": "Kozhikode to MAnjeshwar(Kasargode)", "lat": None, "lon": None},
    {"station_name": "Pappinisseri", "station_code": "PPNS", "route": "Kozhikode to MAnjeshwar(Kasargode)", "lat": None, "lon": None},
    {"station_name": "Kannapuram", "station_code": "KPQ", "route": "Kozhikode to MAnjeshwar(Kasargode)", "lat": None, "lon": None},
    {"station_name": "Payangadi", "station_code": "PAZ", "route": "Kozhikode to MAnjeshwar(Kasargode)", "lat": None, "lon": None},
    {"station_name": "Ezhimala (halt)", "station_code": "ELM", "route": "Kozhikode to MAnjeshwar(Kasargode)", "lat": None, "lon": None},
    {"station_name": "Payyanur", "station_code": "PAY", "route": "Kannur to Kasaragod", "lat": None, "lon": None},
    {"station_name": "Trikarpur", "station_code": "TKQ", "route": "Kozhikode to MAnjeshwar(Kasargode)", "lat": None, "lon": None},
    {"station_name": "Chandera", "station_code": "CDRA", "route": "Kozhikode to MAnjeshwar(Kasargode)", "lat": None, "lon": None},
    {"station_name": "Charvattur", "station_code": "CHV", "route": "Kozhikode to MAnjeshwar(Kasargode)", "lat": None, "lon": None},
    {"station_name": "Nileshwar", "station_code": "NLE", "route": "Kannur to Kasaragod", "lat": None, "lon": None},
    {"station_name": "Kanhangad", "station_code": "KZE", "route": "Kannur to Kasaragod", "lat": None, "lon": None},
    {"station_name": "Bekal Fort", "station_code": "BFR", "route": "Kozhikode to MAnjeshwar(Kasargode)", "lat": None, "lon": None},
    {"station_name": "Kotikulam", "station_code": "KQK", "route": "Kozhikode to MAnjeshwar(Kasargode)", "lat": None, "lon": None},
    {"station_name": "Kalanad (halt)", "station_code": "KLAD", "route": "Kozhikode to MAnjeshwar(Kasargode)", "lat": None, "lon": None},
    {"station_name": "Kasaragod", "station_code": "KGQ", "route": "Kannur to Kasaragod"},
    {"station_name": "Kumbala", "station_code": "KMQ", "route": "Kozhikode to MAnjeshwar(Kasargode)", "lat": None, "lon": None},
    {"station_name": "Uppala", "station_code": "UAA", "route": "Kozhikode to MAnjeshwar(Kasargode)", "lat": None, "lon": None},
    {"station_name": "Manjeshwar", "station_code": "MJS", "route": "Kozhikode to MAnjeshwar(Kasargode)", "lat": None, "lon": None},
     {"station_name": "Palakkad Jn (Olavakkode)", "station_code": "PGT", "route": "SHornur to Minatchipuram(via Palakkad)", "lat": None, "lon": None},
    {"station_name": "Palakkad Town", "station_code": "PGTN", "route": "SHornur to Minatchipuram(via Palakkad)", "lat": None, "lon": None},
    {"station_name": "Pudunagaram", "station_code": "PDGM", "route": "SHornur to Minatchipuram(via Palakkad)", "lat": None, "lon": None},
    {"station_name": "Vadakannikapuram", "station_code": "VDK", "route": "SHornur to Minatchipuram(via Palakkad)", "lat": None, "lon": None},
    {"station_name": "Kollengode", "station_code": "KLGD", "route": "SHornur to Minatchipuram(via Palakkad)", "lat": None, "lon": None},
    {"station_name": "Muthalamada", "station_code": "MMDA", "route": "SHornur to Minatchipuram(via Palakkad)", "lat": None, "lon": None},
    {"station_name": "Minatchipuram", "station_code": "MXM", "route": "SHornur to Minatchipuram(via Palakkad)", "lat": None, "lon": None},
     {"station_name": "Vadanamkurishi (halt)", "station_code": "VDKS", "route": "Shornur to Nilambur", "lat": None, "lon": None},
    {"station_name": "Vallapuzha", "station_code": "VPZ", "route": "Shornur to Nilambur", "lat": None, "lon": None},
    {"station_name": "Kulukkallur", "station_code": "KZC", "route": "Shornur to Nilambur", "lat": None, "lon": None},
    {"station_name": "Cherukara", "station_code": "CQA", "route": "Shornur to Nilambur", "lat": None, "lon": None},
    {"station_name": "Angadippuram", "station_code": "AAM", "route": "Shornur to Nilambur", "lat": None, "lon": None},
    {"station_name": "Pattikkad", "station_code": "PKQ", "route": "Shornur to Nilambur", "lat": None, "lon": None},
    {"station_name": "Melattur", "station_code": "MLTR", "route": "Shornur to Nilambur", "lat": None, "lon": None},
    {"station_name": "Tuvvur", "station_code": "TUV", "route": "Shornur to Nilambur", "lat": None, "lon": None},
    {"station_name": "Todiyappulam (halt)", "station_code": "TDPM", "route": "Shornur to Nilambur", "lat": None, "lon": None},
    {"station_name": "Vaniyambalam", "station_code": "VNB", "route": "Shornur to Nilambur", "lat": None, "lon": None},
    {"station_name": "Nilambur Road", "station_code": "NIL", "route": "Shornur to Nilambur"}
]

def geocode_stations(stations, google_maps_api_key):
    """
    Geocodes railway stations using the Google Maps Geocoding API and updates lat/lon.
    """
    gmaps = googlemaps.Client(key=google_maps_api_key)

    for station in stations:
        try:
            geocode_result = gmaps.geocode(station['station_name'] + ", Kerala, India")

            if geocode_result:
                location = geocode_result[0]['geometry']['location']
                station['lat'] = location['lat']
                station['lon'] = location['lng']
                print(f"Geocoded {station['station_name']}: {station['lat']}, {station['lon']}")
            else:
                print(f"Could not geocode {station['station_name']}")
                station['lat'] = None
                station['lon'] = None

        except Exception as e:
            print(f"Error geocoding {station['station_name']}: {e}")
            station['lat'] = None
            station['lon'] = None

        time.sleep(0.2)  # Respect Rate Limit

    return stations

def save_stations_to_json(stations, filename="kerala_railway_stations.json"):
    """Saves the railway station data to a JSON file."""
        # Ensure the directory exists
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(stations, f, indent=4, ensure_ascii=False)  # Save Json with pretty formatting and Unicode support

if __name__ == '__main__':
    #HTML_FILE = r'I:\Downloads\Kerala Railway Stations Tapioca.html'  # Replace with your file path
    OUTPUT_JSON = r"H:\RGTApp\RGT\backend\kerala_railway_stations.json" # Full PAth!
    GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")  # Replace with your API key
    if not GOOGLE_MAPS_API_KEY:
        print("Error: GOOGLE_MAPS_API_KEY not found in environment variables. Set this with .env")
        exit()

    #all_stations = extract_station_data(HTML_FILE) # No Longer needed
    geolocated_stations = geocode_stations(stations_data, GOOGLE_MAPS_API_KEY)
    save_stations_to_json(geolocated_stations, OUTPUT_JSON)

    print(f"Geocoded, and saved {len(geolocated_stations)} stations to {OUTPUT_JSON}")