from __future__ import annotations

CATEGORIES = [
    {"code": "INCOME", "name": "Income (group)", "type": "income", "parent": None, "budgetable": False, "active": True},
    {"code": "HOUSING", "name": "Housing (group)", "type": "expense", "parent": None, "budgetable": False, "active": True},
    {"code": "INCOME_SALARY", "name": "Salary", "type": "income", "parent": "INCOME", "budgetable": False, "active": True},
    {"code": "INCOME_OTHER", "name": "Other Income", "type": "income", "parent": "INCOME", "budgetable": False, "active": True},
    {"code": "HOUSING_RENT", "name": "Rent", "type": "expense", "parent": "HOUSING", "budgetable": True, "active": True},
    {"code": "UTILITIES", "name": "Utilities", "type": "expense", "parent": None, "budgetable": True, "active": True},
    {"code": "GROCERY", "name": "Groceries", "type": "expense", "parent": None, "budgetable": True, "active": True},
    {"code": "DINING", "name": "Dining and Restaurants", "type": "expense", "parent": None, "budgetable": True, "active": True},
    {"code": "TRANSPORT", "name": "Transportation", "type": "expense", "parent": None, "budgetable": True, "active": True},
    {"code": "SUBSCRIPTION", "name": "Subscriptions", "type": "expense", "parent": None, "budgetable": True, "active": True},
    {"code": "SHOPPING", "name": "Shopping", "type": "expense", "parent": None, "budgetable": True, "active": True},
    {"code": "HEALTH", "name": "Healthcare", "type": "expense", "parent": None, "budgetable": True, "active": True},
    {"code": "ENTERTAINMENT", "name": "Entertainment", "type": "expense", "parent": None, "budgetable": True, "active": True},
    {"code": "TRAVEL", "name": "Travel", "type": "expense", "parent": None, "budgetable": True, "active": True},
    {"code": "INSURANCE", "name": "Insurance", "type": "expense", "parent": None, "budgetable": True, "active": True},
    {"code": "EDUCATION", "name": "Education", "type": "expense", "parent": None, "budgetable": True, "active": True},
    {"code": "FEES", "name": "Bank Fees", "type": "expense", "parent": None, "budgetable": True, "active": True},
    {"code": "TRANSFER", "name": "Internal Transfer", "type": "transfer", "parent": None, "budgetable": False, "active": True},
    {"code": "REFUND", "name": "Refund", "type": "refund", "parent": None, "budgetable": False, "active": True},
    {"code": "OTHER", "name": "Uncategorized", "type": "expense", "parent": None, "budgetable": True, "active": True},
    {"code": "FOOD", "name": "Food (legacy)", "type": "expense", "parent": None, "budgetable": False, "active": False},
    {"code": "TRANSPORTATION", "name": "Transportation (legacy)", "type": "expense", "parent": None, "budgetable": False, "active": False},
    {"code": "SUBSCRIPTIONS", "name": "Subscriptions (legacy)", "type": "expense", "parent": None, "budgetable": False, "active": False},
    {"code": "UTIL", "name": "Utilities (legacy)", "type": "expense", "parent": None, "budgetable": False, "active": False},
    {"code": "MISC", "name": "Miscellaneous (legacy)", "type": "expense", "parent": None, "budgetable": False, "active": False},
]

LEGACY_CATEGORY_ALIASES = {
    "FOOD": ("GROCERY", "Legacy umbrella split into GROCERY and DINING; GROCERY is the effective default."),
    "TRANSPORTATION": ("TRANSPORT", "Renamed in taxonomy v2025.1."),
    "SUBSCRIPTIONS": ("SUBSCRIPTION", "Plural form retired in taxonomy v2025.1."),
    "UTIL": ("UTILITIES", "Abbreviation retired in taxonomy v2025.1."),
    "MISC": ("OTHER", "Legacy miscellaneous bucket merged into OTHER."),
}

MERCHANTS = [
    {"key": "acme_corp", "name": "Acme Corporation", "category": "INCOME_SALARY", "aliases": ["ACME CORP PAYROLL", "DIRECT DEP ACME CORP", "ACME CORP"], "mcc": "0000", "online": 0.0, "subscription": False, "weight": 3.0, "bias": 0},
    {"key": "globex_llc", "name": "Globex LLC", "category": "INCOME_SALARY", "aliases": ["GLOBEX LLC PAYROLL", "DIRECT DEP GLOBEX", "GLOBEX LLC"], "mcc": "0000", "online": 0.0, "subscription": False, "weight": 2.0, "bias": 0},
    {"key": "initech", "name": "Initech Inc", "category": "INCOME_SALARY", "aliases": ["INITECH PAYROLL", "DIRECT DEP INITECH", "INITECH INC"], "mcc": "0000", "online": 0.0, "subscription": False, "weight": 2.0, "bias": 0},
    {"key": "umbrella", "name": "Umbrella Group", "category": "INCOME_SALARY", "aliases": ["UMBRELLA GROUP PAYROLL", "DIRECT DEP UMBRELLA", "UMBRELLA GROUP"], "mcc": "0000", "online": 0.0, "subscription": False, "weight": 1.5, "bias": 0},
    {"key": "harbor_property", "name": "Harbor Property Management", "category": "HOUSING_RENT", "aliases": ["HARBOR PROPERTY RENT", "HARBOR PMT RENT", "HARBOR PROPERTY MGMT"], "mcc": "6513", "online": 0.3, "subscription": False, "weight": 3.0, "bias": 0},
    {"key": "oakwood_apts", "name": "Oakwood Apartments", "category": "HOUSING_RENT", "aliases": ["OAKWOOD APTS RENT", "OAKWOOD RENT PAYMENT", "OAKWOOD APARTMENTS"], "mcc": "6513", "online": 0.2, "subscription": False, "weight": 2.0, "bias": 0},
    {"key": "skyline_rentals", "name": "Skyline Rentals", "category": "HOUSING_RENT", "aliases": ["SKYLINE RENTALS RENT", "SKYLINE PMT", "SKYLINE RENTALS"], "mcc": "6513", "online": 0.3, "subscription": False, "weight": 1.5, "bias": 0},
    {"key": "whole_foods", "name": "Whole Foods Market", "category": "GROCERY", "aliases": ["WHOLEFDS", "WHOLE FOODS MKT", "WFM"], "mcc": "5411", "online": 0.1, "subscription": False, "weight": 2.5, "bias": 0},
    {"key": "safeway", "name": "Safeway", "category": "GROCERY", "aliases": ["SAFEWAY", "SAFEWAY STORE", "SAFEWAY INC"], "mcc": "5411", "online": 0.1, "subscription": False, "weight": 3.0, "bias": 0},
    {"key": "trader_joes", "name": "Trader Joes", "category": "GROCERY", "aliases": ["TRADER JOES", "TRADER JOES #", "TRADER JOE'S"], "mcc": "5411", "online": 0.0, "subscription": False, "weight": 2.0, "bias": 0},
    {"key": "kroger", "name": "Kroger", "category": "GROCERY", "aliases": ["KROGER", "KROGER STORE", "KROGER FUEL"], "mcc": "5411", "online": 0.1, "subscription": False, "weight": 2.0, "bias": 0},
    {"key": "costco", "name": "Costco Wholesale", "category": "GROCERY", "aliases": ["COSTCO WHSE", "COSTCO", "COSTCO GAS"], "mcc": "5300", "online": 0.1, "subscription": False, "weight": 1.5, "bias": 0},
    {"key": "walmart", "name": "Walmart", "category": "GROCERY", "aliases": ["WALMART", "WAL-MART", "WALMART SUPERCENTER"], "mcc": "5411", "online": 0.2, "subscription": False, "weight": 1.5, "bias": 0},
    {"key": "farmers_market", "name": "City Farmers Market", "category": "GROCERY", "aliases": ["FARMERS MARKET", "CITY FARMERS MKT", "FM MARKET"], "mcc": "5499", "online": 0.0, "subscription": False, "weight": 0.8, "bias": 0},
    {"key": "starbucks", "name": "Starbucks", "category": "DINING", "aliases": ["STARBUCKS", "STARBUCKS STORE", "SBUX"], "mcc": "5814", "online": 0.2, "subscription": False, "weight": 3.0, "bias": 0},
    {"key": "mcdonalds", "name": "McDonalds", "category": "DINING", "aliases": ["MCDONALDS", "MCDONALD'S", "MCD"], "mcc": "5814", "online": 0.2, "subscription": False, "weight": 2.2, "bias": 0},
    {"key": "chipotle", "name": "Chipotle", "category": "DINING", "aliases": ["CHIPOTLE", "CHIPOTLE MEX GRILL", "CHIPOTLE #"], "mcc": "5814", "online": 0.3, "subscription": False, "weight": 2.0, "bias": 0},
    {"key": "local_bistro", "name": "Local Bistro", "category": "DINING", "aliases": ["LOCAL BISTRO", "BISTRO 22", "LOCAL BISTRO LLC"], "mcc": "5812", "online": 0.0, "subscription": False, "weight": 0.8, "bias": 0},
    {"key": "doordash", "name": "DoorDash", "category": "DINING", "aliases": ["DOORDASH", "DD DOORDASH", "DOORDASH INC"], "mcc": "5812", "online": 1.0, "subscription": False, "weight": 2.0, "bias": 0},
    {"key": "uber_eats", "name": "Uber Eats", "category": "DINING", "aliases": ["UBER EATS", "UBER *EATS", "UBER"], "mcc": "5812", "online": 1.0, "subscription": False, "weight": 1.5, "bias": 30},
    {"key": "panera", "name": "Panera Bread", "category": "DINING", "aliases": ["PANERA BREAD", "PANERA", "PANERA #"], "mcc": "5814", "online": 0.2, "subscription": False, "weight": 1.2, "bias": 0},
    {"key": "sushi_bar", "name": "Sushi Bar", "category": "DINING", "aliases": ["SUSHI BAR", "SUSHI HOUSE", "SUSHI BAR 88"], "mcc": "5812", "online": 0.0, "subscription": False, "weight": 0.7, "bias": 0},
    {"key": "uber_trip", "name": "Uber", "category": "TRANSPORT", "aliases": ["UBER *TRIP", "UBER TRIP", "UBER"], "mcc": "4121", "online": 1.0, "subscription": False, "weight": 2.0, "bias": 20},
    {"key": "lyft", "name": "Lyft", "category": "TRANSPORT", "aliases": ["LYFT", "LYFT RIDE", "LYFT INC"], "mcc": "4121", "online": 1.0, "subscription": False, "weight": 1.2, "bias": 0},
    {"key": "shell", "name": "Shell", "category": "TRANSPORT", "aliases": ["SHELL OIL", "SHELL", "SHELL SERVICE"], "mcc": "5541", "online": 0.0, "subscription": False, "weight": 2.2, "bias": 0},
    {"key": "chevron", "name": "Chevron", "category": "TRANSPORT", "aliases": ["CHEVRON", "CHEVRON USA", "CHEVRON #"], "mcc": "5541", "online": 0.0, "subscription": False, "weight": 2.0, "bias": 0},
    {"key": "metro_transit", "name": "Metro Transit", "category": "TRANSPORT", "aliases": ["METRO TRANSIT", "METRO CARD", "TRANSIT AUTHORITY"], "mcc": "4111", "online": 0.2, "subscription": False, "weight": 1.5, "bias": 0},
    {"key": "parking_garage", "name": "City Parking", "category": "TRANSPORT", "aliases": ["CITY PARKING", "PARKING GARAGE", "PARKMOBILE"], "mcc": "7523", "online": 0.4, "subscription": False, "weight": 1.0, "bias": 0},
    {"key": "exxon", "name": "Exxon", "category": "TRANSPORT", "aliases": ["EXXON", "EXXONMOBIL", "EXXON #"], "mcc": "5541", "online": 0.0, "subscription": False, "weight": 1.5, "bias": 0},
    {"key": "pgande", "name": "Pacific Gas and Electric", "category": "UTILITIES", "aliases": ["PGANDE", "PG&E WEB ONLINE", "PG&E"], "mcc": "4900", "online": 0.5, "subscription": False, "weight": 2.0, "bias": 0},
    {"key": "city_water", "name": "City Water Utility", "category": "UTILITIES", "aliases": ["CITY WATER UTIL", "CITY WATER", "MUNICIPAL WATER"], "mcc": "4900", "online": 0.4, "subscription": False, "weight": 1.5, "bias": 0},
    {"key": "comcast", "name": "Comcast", "category": "UTILITIES", "aliases": ["COMCAST", "XFINITY", "COMCAST CABLE"], "mcc": "4899", "online": 0.6, "subscription": False, "weight": 2.0, "bias": 0},
    {"key": "verizon", "name": "Verizon", "category": "UTILITIES", "aliases": ["VERIZON WIRELESS", "VERIZON", "VZWRLSS"], "mcc": "4814", "online": 0.6, "subscription": False, "weight": 2.0, "bias": 0},
    {"key": "att", "name": "AT&T", "category": "UTILITIES", "aliases": ["AT&T WIRELESS", "AT&T", "ATT PAYMENT"], "mcc": "4814", "online": 0.6, "subscription": False, "weight": 1.5, "bias": 0},
    {"key": "netflix", "name": "Netflix", "category": "SUBSCRIPTION", "aliases": ["NETFLIX.COM", "NETFLIX", "NETFLIX SUBSCRIPTION"], "mcc": "4899", "online": 1.0, "subscription": True, "weight": 3.0, "bias": 0},
    {"key": "spotify", "name": "Spotify", "category": "SUBSCRIPTION", "aliases": ["SPOTIFY USA", "SPOTIFY", "SPOTIFY P"], "mcc": "5815", "online": 1.0, "subscription": True, "weight": 2.5, "bias": 0},
    {"key": "disney_plus", "name": "Disney Plus", "category": "SUBSCRIPTION", "aliases": ["DISNEY PLUS", "DISNEY+", "DISNEY SUBSCRIPTION"], "mcc": "4899", "online": 1.0, "subscription": True, "weight": 1.5, "bias": 0},
    {"key": "icloud", "name": "Apple iCloud", "category": "SUBSCRIPTION", "aliases": ["APPLE ICLOUD", "ICLOUD STORAGE", "APPLE.COM/BILL"], "mcc": "5815", "online": 1.0, "subscription": True, "weight": 2.0, "bias": 0},
    {"key": "amazon_prime", "name": "Amazon Prime", "category": "SUBSCRIPTION", "aliases": ["AMZN PRIME", "AMAZON PRIME", "AMAZON"], "mcc": "4899", "online": 1.0, "subscription": True, "weight": 1.8, "bias": 40},
    {"key": "nytimes", "name": "New York Times", "category": "SUBSCRIPTION", "aliases": ["NYTIMES", "NYT SUBSCRIPTION", "NEW YORK TIMES"], "mcc": "5815", "online": 1.0, "subscription": True, "weight": 1.2, "bias": 0},
    {"key": "gym_fit", "name": "FitLife Gym", "category": "HEALTH", "aliases": ["FITLIFE GYM", "FITLIFE", "FITLIFE FITNESS"], "mcc": "7997", "online": 0.4, "subscription": True, "weight": 1.0, "bias": 0},
    {"key": "cloud_storage", "name": "Cloud Storage Co", "category": "SUBSCRIPTION", "aliases": ["CLOUDSTORAGE", "CLOUD STORAGE CO", "CLOUDSTORE"], "mcc": "5815", "online": 1.0, "subscription": True, "weight": 1.2, "bias": 0},
    {"key": "kindle_unltd", "name": "Kindle Unlimited", "category": "SUBSCRIPTION", "aliases": ["KINDLE UNLTD", "KINDLE UNLIMITED", "AMZN KINDLE"], "mcc": "5815", "online": 1.0, "subscription": True, "weight": 1.0, "bias": 0},
    {"key": "amazon_mktp", "name": "Amazon Marketplace", "category": "SHOPPING", "aliases": ["AMZN MKTP US", "AMAZON.COM", "AMAZON"], "mcc": "5999", "online": 1.0, "subscription": False, "weight": 3.0, "bias": 10},
    {"key": "target", "name": "Target", "category": "SHOPPING", "aliases": ["TARGET", "TARGET STORE", "TARGET #"], "mcc": "5310", "online": 0.3, "subscription": False, "weight": 2.5, "bias": 0},
    {"key": "bestbuy", "name": "Best Buy", "category": "SHOPPING", "aliases": ["BESTBUY", "BEST BUY", "BESTBUY #"], "mcc": "5732", "online": 0.5, "subscription": False, "weight": 1.5, "bias": 0},
    {"key": "ikea", "name": "IKEA", "category": "SHOPPING", "aliases": ["IKEA", "IKEA STORE", "IKEA HOME"], "mcc": "5712", "online": 0.4, "subscription": False, "weight": 1.0, "bias": 0},
    {"key": "home_depot", "name": "Home Depot", "category": "SHOPPING", "aliases": ["HOME DEPOT", "HOMEDEPOT", "HOME DEPOT #"], "mcc": "5211", "online": 0.3, "subscription": False, "weight": 1.3, "bias": 0},
    {"key": "zara", "name": "Zara", "category": "SHOPPING", "aliases": ["ZARA USA", "ZARA", "ZARA STORE"], "mcc": "5651", "online": 0.4, "subscription": False, "weight": 0.9, "bias": 0},
    {"key": "etsy", "name": "Etsy", "category": "SHOPPING", "aliases": ["ETSY.COM", "ETSY", "ETSY INC"], "mcc": "5999", "online": 1.0, "subscription": False, "weight": 0.8, "bias": 0},
    {"key": "apple_store", "name": "Apple Store", "category": "SHOPPING", "aliases": ["APPLE STORE", "APPLE.COM", "APPLE INC"], "mcc": "5732", "online": 0.7, "subscription": False, "weight": 1.2, "bias": 0},
    {"key": "cvs", "name": "CVS Pharmacy", "category": "HEALTH", "aliases": ["CVS PHARMACY", "CVS", "CVS #"], "mcc": "5912", "online": 0.2, "subscription": False, "weight": 2.5, "bias": 0},
    {"key": "walgreens", "name": "Walgreens", "category": "HEALTH", "aliases": ["WALGREENS", "WALGREENS #", "WALGREENS PHARMACY"], "mcc": "5912", "online": 0.2, "subscription": False, "weight": 2.0, "bias": 0},
    {"key": "city_clinic", "name": "City Clinic", "category": "HEALTH", "aliases": ["CITY CLINIC", "CITY MEDICAL", "CLINIC PAYMENT"], "mcc": "8011", "online": 0.1, "subscription": False, "weight": 0.9, "bias": 0},
    {"key": "dental_care", "name": "Dental Care", "category": "HEALTH", "aliases": ["DENTAL CARE", "DENTAL ASSOC", "DENTIST OFFICE"], "mcc": "8021", "online": 0.1, "subscription": False, "weight": 0.7, "bias": 0},
    {"key": "local_pharmacy", "name": "Local Pharmacy", "category": "HEALTH", "aliases": ["LOCAL PHARMACY", "PHARMACY", "RX LOCAL"], "mcc": "5912", "online": 0.1, "subscription": False, "weight": 0.8, "bias": 0},
    {"key": "amc_cinema", "name": "AMC Theatres", "category": "ENTERTAINMENT", "aliases": ["AMC CINEMA", "AMC THEATRES", "AMC #"], "mcc": "7832", "online": 0.3, "subscription": False, "weight": 1.5, "bias": 0},
    {"key": "steam", "name": "Steam Games", "category": "ENTERTAINMENT", "aliases": ["STEAM GAMES", "STEAM", "STEAM PURCHASE"], "mcc": "5816", "online": 1.0, "subscription": False, "weight": 1.3, "bias": 0},
    {"key": "live_nation", "name": "Live Nation", "category": "ENTERTAINMENT", "aliases": ["LIVE NATION", "TICKETMASTER", "LIVE NATION TIX"], "mcc": "7922", "online": 0.7, "subscription": False, "weight": 1.0, "bias": 0},
    {"key": "bowling_alley", "name": "City Bowling", "category": "ENTERTAINMENT", "aliases": ["CITY BOWLING", "BOWLING ALLEY", "LUCKY STRIKE"], "mcc": "7933", "online": 0.1, "subscription": False, "weight": 0.7, "bias": 0},
    {"key": "delta_air", "name": "Delta Air Lines", "category": "TRAVEL", "aliases": ["DELTA AIR", "DELTA AIR LINES", "DELTA"], "mcc": "4511", "online": 0.9, "subscription": False, "weight": 1.5, "bias": 0},
    {"key": "marriott", "name": "Marriott", "category": "TRAVEL", "aliases": ["MARRIOTT", "MARRIOTT HOTELS", "MARRIOTT BONVOY"], "mcc": "7011", "online": 0.7, "subscription": False, "weight": 1.3, "bias": 0},
    {"key": "airbnb", "name": "Airbnb", "category": "TRAVEL", "aliases": ["AIRBNB", "AIRBNB.COM", "AIRBNB INC"], "mcc": "7011", "online": 1.0, "subscription": False, "weight": 1.2, "bias": 0},
    {"key": "expedia", "name": "Expedia", "category": "TRAVEL", "aliases": ["EXPEDIA", "EXPEDIA.COM", "EXPEDIA TRAVEL"], "mcc": "4722", "online": 1.0, "subscription": False, "weight": 1.0, "bias": 0},
    {"key": "state_farm", "name": "State Farm", "category": "INSURANCE", "aliases": ["STATE FARM", "STATE FARM INS", "STATEFARM"], "mcc": "6300", "online": 0.4, "subscription": False, "weight": 1.5, "bias": 0},
    {"key": "geico", "name": "Geico", "category": "INSURANCE", "aliases": ["GEICO", "GEICO AUTO", "GEICO INSURANCE"], "mcc": "6300", "online": 0.5, "subscription": False, "weight": 1.3, "bias": 0},
    {"key": "blue_cross", "name": "Blue Cross", "category": "INSURANCE", "aliases": ["BLUE CROSS", "BLUECROSS", "BLUE CROSS BLUE SHIELD"], "mcc": "6300", "online": 0.3, "subscription": False, "weight": 1.0, "bias": 0},
    {"key": "state_university", "name": "State University", "category": "EDUCATION", "aliases": ["STATE UNIVERSITY", "UNIV PAYMENT", "STATE UNIV"], "mcc": "8220", "online": 0.5, "subscription": False, "weight": 1.0, "bias": 0},
    {"key": "coursera", "name": "Coursera", "category": "EDUCATION", "aliases": ["COURSERA", "COURSERA.ORG", "COURSERA INC"], "mcc": "8299", "online": 1.0, "subscription": False, "weight": 1.0, "bias": 0},
    {"key": "udemy", "name": "Udemy", "category": "EDUCATION", "aliases": ["UDEMY", "UDEMY.COM", "UDEMY INC"], "mcc": "8299", "online": 1.0, "subscription": False, "weight": 0.8, "bias": 0},
    {"key": "bank_fee", "name": "First Bank Service Fee", "category": "FEES", "aliases": ["MONTHLY SERVICE FEE", "BANK SERVICE FEE", "ACCOUNT FEE"], "mcc": "6010", "online": 0.0, "subscription": False, "weight": 2.0, "bias": 0},
    {"key": "atm_fee", "name": "ATM Fee", "category": "FEES", "aliases": ["ATM FEE", "ATM WITHDRAWAL FEE", "NON-NETWORK ATM"], "mcc": "6011", "online": 0.0, "subscription": False, "weight": 1.0, "bias": 0},
    {"key": "overdraft_fee", "name": "Overdraft Fee", "category": "FEES", "aliases": ["OVERDRAFT FEE", "NSF FEE", "RETURNED ITEM FEE"], "mcc": "6010", "online": 0.0, "subscription": False, "weight": 0.5, "bias": 0},
    {"key": "sq_local", "name": "Square Local Merchant", "category": "OTHER", "aliases": ["SQ *LOCAL SHOP", "SQUARE *MARKET", "SQ *"], "mcc": "5999", "online": 0.1, "subscription": False, "weight": 1.5, "bias": 0},
    {"key": "misc_online", "name": "Misc Online Merchant", "category": "OTHER", "aliases": ["MISC ONLINE", "WEB PMT", "ONLINE PURCHASE"], "mcc": "5999", "online": 1.0, "subscription": False, "weight": 1.2, "bias": 0},
    {"key": "charity", "name": "Community Charity", "category": "OTHER", "aliases": ["COMMUNITY CHARITY", "DONATION", "CHARITY PAYMENT"], "mcc": "8398", "online": 0.5, "subscription": False, "weight": 0.6, "bias": 0},
    {"key": "post_office", "name": "Post Office", "category": "OTHER", "aliases": ["POST OFFICE", "USPS", "POSTAL SERVICE"], "mcc": "9402", "online": 0.1, "subscription": False, "weight": 0.8, "bias": 0},
    {"key": "pet_store", "name": "Pet Store", "category": "SHOPPING", "aliases": ["PET STORE", "PETCO", "PETSMART"], "mcc": "5995", "online": 0.2, "subscription": False, "weight": 0.9, "bias": 0},
    {"key": "hardware_store", "name": "Hardware Store", "category": "SHOPPING", "aliases": ["HARDWARE STORE", "ACE HARDWARE", "TRUE VALUE"], "mcc": "5251", "online": 0.1, "subscription": False, "weight": 0.8, "bias": 0},
    {"key": "upwork", "name": "Upwork", "category": "INCOME_OTHER", "aliases": ["UPWORK PAYMENT", "UPWORK", "FREELANCE PAYOUT"], "mcc": "0000", "online": 1.0, "subscription": False, "weight": 1.5, "bias": 0},
    {"key": "bank_interest", "name": "First Bank Interest", "category": "INCOME_OTHER", "aliases": ["INTEREST PAYMENT", "BANK INTEREST", "SAVINGS INTEREST"], "mcc": "0000", "online": 0.0, "subscription": False, "weight": 1.0, "bias": 0},
    {"key": "rewards_credit", "name": "Card Rewards", "category": "INCOME_OTHER", "aliases": ["CASH BACK REWARD", "REWARDS CREDIT", "CARD CASHBACK"], "mcc": "0000", "online": 0.0, "subscription": False, "weight": 0.8, "bias": 0},
]

CATEGORY_MERCHANTS: dict[str, list[dict]] = {}
for merchant in MERCHANTS:
    CATEGORY_MERCHANTS.setdefault(merchant["category"], []).append(merchant)

AMOUNT_PARAMS = {
    "GROCERY": (52.0, 0.50, 7.0, 320.0),
    "DINING": (27.0, 0.60, 5.0, 180.0),
    "TRANSPORT": (21.0, 0.72, 3.0, 160.0),
    "UTILITIES": (88.0, 0.38, 35.0, 260.0),
    "SHOPPING": (62.0, 0.78, 8.0, 650.0),
    "HEALTH": (43.0, 0.70, 8.0, 450.0),
    "ENTERTAINMENT": (36.0, 0.68, 6.0, 280.0),
    "TRAVEL": (430.0, 0.80, 80.0, 3200.0),
    "INSURANCE": (146.0, 0.22, 60.0, 380.0),
    "EDUCATION": (135.0, 0.75, 20.0, 900.0),
    "FEES": (12.0, 0.55, 2.0, 45.0),
    "OTHER": (34.0, 0.85, 4.0, 350.0),
    "INCOME_OTHER": (420.0, 0.80, 20.0, 3000.0),
    "SUBSCRIPTION": (15.0, 0.35, 3.0, 60.0),
    "HOUSING_RENT": (1800.0, 0.20, 700.0, 4500.0),
    "INCOME_SALARY": (5200.0, 0.30, 2000.0, 16000.0),
}

SEASONAL_SHOPPING = [0.82, 0.80, 0.90, 0.95, 0.98, 0.95, 0.90, 0.98, 1.00, 1.05, 1.26, 1.40]
SEASONAL_TRAVEL = [0.70, 0.62, 0.85, 1.00, 1.15, 1.45, 1.62, 1.50, 1.02, 0.92, 0.88, 1.20]
SEASONAL_DINING = [0.88, 0.86, 0.94, 0.98, 1.00, 1.02, 1.05, 1.04, 0.98, 1.00, 1.08, 1.20]
SEASONAL_GROCERY = [0.96, 0.94, 0.98, 1.00, 1.01, 1.02, 1.01, 1.00, 1.00, 1.02, 1.10, 1.16]

CATEGORY_SEASONALITY = {
    "SHOPPING": SEASONAL_SHOPPING,
    "TRAVEL": SEASONAL_TRAVEL,
    "DINING": SEASONAL_DINING,
    "GROCERY": SEASONAL_GROCERY,
    "ENTERTAINMENT": [0.9, 0.85, 0.95, 1.0, 1.05, 1.12, 1.18, 1.10, 0.95, 1.0, 1.05, 1.15],
    "UTILITIES": [1.15, 1.12, 1.02, 0.92, 0.88, 0.95, 1.08, 1.12, 1.00, 0.92, 0.98, 1.10],
}

RECURRING_MERCHANT_KEYS = [
    "acme_corp", "globex_llc", "initech", "umbrella",
    "harbor_property", "oakwood_apts", "skyline_rentals",
    "netflix", "spotify", "disney_plus", "icloud", "amazon_prime", "nytimes",
    "cloud_storage", "kindle_unltd", "gym_fit",
]

SUBSCRIPTION_KEYS = ["netflix", "spotify", "disney_plus", "icloud", "amazon_prime", "nytimes", "cloud_storage", "kindle_unltd", "gym_fit"]

BUDGET_SHARES = {
    "HOUSING_RENT": 0.24,
    "UTILITIES": 0.055,
    "GROCERY": 0.115,
    "DINING": 0.075,
    "TRANSPORT": 0.065,
    "SUBSCRIPTION": 0.020,
    "SHOPPING": 0.060,
    "HEALTH": 0.040,
    "ENTERTAINMENT": 0.030,
    "TRAVEL": 0.040,
    "INSURANCE": 0.032,
    "EDUCATION": 0.020,
}

BUDGET_CATEGORY_SETS = [
    ["HOUSING_RENT", "UTILITIES", "GROCERY", "DINING", "TRANSPORT", "SUBSCRIPTION", "SHOPPING", "HEALTH", "ENTERTAINMENT", "TRAVEL", "INSURANCE"],
    ["HOUSING_RENT", "UTILITIES", "GROCERY", "DINING", "TRANSPORT", "SUBSCRIPTION", "SHOPPING", "HEALTH", "ENTERTAINMENT", "TRAVEL"],
    ["UTILITIES", "GROCERY", "DINING", "TRANSPORT", "SUBSCRIPTION", "SHOPPING", "HEALTH", "ENTERTAINMENT", "TRAVEL", "INSURANCE"],
    ["HOUSING_RENT", "UTILITIES", "GROCERY", "DINING", "TRANSPORT", "SUBSCRIPTION", "SHOPPING", "HEALTH", "ENTERTAINMENT", "TRAVEL", "INSURANCE", "EDUCATION"],
    ["HOUSING_RENT", "UTILITIES", "GROCERY", "DINING", "TRANSPORT", "SHOPPING", "HEALTH", "TRAVEL"],
]

CATEGORY_BY_CODE = {c["code"]: c for c in CATEGORIES}
MERCHANT_BY_KEY = {m["key"]: m for m in MERCHANTS}


def category_type(code: str) -> str:
    item = CATEGORY_BY_CODE.get(code)
    return item["type"] if item else "expense"


def is_active_category(code: str) -> bool:
    item = CATEGORY_BY_CODE.get(code)
    return bool(item and item["active"])
