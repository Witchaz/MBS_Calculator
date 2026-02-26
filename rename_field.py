from firebase_admin import firestore

from infrastructure.firebase_client import init_firebase

db = init_firebase()

SAFETY = 0 

OLD_COLUMNS_NAME = ""
NEW_COLUMNS_NAME = ""
 
games_ref = db.collection("mbs_games")

for game_doc in games_ref.stream():

    rounds_ref = game_doc.reference.collection("rounds").stream()

    for round_doc in rounds_ref:
        data = round_doc.to_dict()

        production_list = data.get("production", [])

        if not production_list:
            continue

        updated = False
        new_production = []

        for item in production_list:

            if OLD_COLUMNS_NAME in item:
                item[NEW_COLUMNS_NAME] = item[OLD_COLUMNS_NAME]
                del item[OLD_COLUMNS_NAME]
                updated = True

            new_production.append(item)

        if updated:
            round_doc.reference.update({
                "production": new_production
            })

            print(f"Updated {game_doc.id} / {round_doc.id}")