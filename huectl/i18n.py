"""Minimal internationalization (English default, French optional)."""

STRINGS = {
    "en": {
        "refresh_tt": "Refresh", "settings_tt": "Settings",
        "loading": "Loading...",
        "add_room": "Room", "add_zone": "Zone",
        "add_room_tt": "New room - groups devices (a lamp lives in one room)",
        "add_zone_tt": "New zone - groups lights freely (zones may overlap)",
        "badge_room": "ROOM", "badge_zone": "ZONE",
        "edit_btn": "Edit", "delete_btn": "Delete",
        "scenes": "Scenes", "lights": "Lights", "all_group": "Whole group",
        "others": "Others", "other_scenes": "Other scenes",
        "new_scene_tt": "New scene in this group",
        "scene_activated": "Scene: {name}", "vide": "empty",
        "tile_lamps": "{n} lamp(s)", "scene_empty": " (empty scene)",
        "menu_activate": "Activate", "menu_edit": "Edit...",
        "menu_delete": "Delete...", "toggle_tt": "Turn on / off",
        "title_new_scene": "New scene", "title_edit_scene": "Edit scene",
        "name": "Name", "room_zone": "Room / zone",
        "capture_new": "Capture the current state of the lights",
        "capture_edit": "Replace colors with the current state of the lights",
        "editor_tip": "Set your lights first (colors, brightness), "
                      "then the scene remembers this state.",
        "cancel": "Cancel", "save": "Save", "scene_default": "Scene",
        "del_scene_title": "Delete scene",
        "del_scene_msg": "Delete '{name}'? This cannot be undone.",
        "no_lamp_group": "This group has no lamp.",
        "saving": "Saving...", "deleting": "Deleting...",
        "title_new_zone": "New zone", "title_edit_zone": "Edit zone",
        "title_new_room": "New room", "title_edit_room": "Edit room",
        "zone_lights": "Lights in this zone",
        "room_devices": "Devices in this room",
        "zone_hint": "A zone groups lights across rooms. Zones may overlap and "
                     "a light can belong to several.",
        "room_hint": "A room mirrors your physical setup and holds devices. "
                     "A lamp belongs to exactly one room.",
        "member_in_room": "{name}  - in {room}",
        "no_members": "Nothing available here.",
        "del_zone_title": "Delete zone",
        "del_zone_msg": "Delete zone '{name}'?",
        "del_room_title": "Delete room",
        "del_room_msg": "Delete room '{name}'? The lamps stay, "
                        "they just leave this room.",
        "room_default": "Room", "zone_default": "Zone",
        "settings_title": "Settings", "bridge_hdr": "Philips Hue bridge",
        "ip_info": "Bridge IP address. Change it if the bridge IP changed "
                   "(the access key stays valid for the same bridge).",
        "repair_btn": "Change bridge / re-pair...",
        "disconnect_btn": "Disconnect from this bridge",
        "disconnect_title": "Disconnect",
        "disconnect_msg": "Forget this bridge and its keys? You'll have to re-pair.",
        "close": "Close", "appearance_hdr": "Appearance",
        "columns_label": "Tiles per row", "language_label": "Language",
        "start_min_label": "Start minimized to tray",
        "setup_title": "Bridge pairing",
        "setup_hdr": "Connect to the Philips Hue bridge",
        "setup_steps": "1.  Detect the bridge (or enter its IP).\n"
                       "2.  Press the big round button on the bridge.\n"
                       "3.  Click 'Pair' within 30 seconds.",
        "detect": "Detect", "pair": "Pair",
        "searching": "Searching for the bridge on the network...",
        "detect_fail": "Auto-detection failed - enter the IP manually.",
        "found": "Bridge found: {ip}.  Press its button then 'Pair'.",
        "none_found": "No bridge detected - enter the IP manually.",
        "press_now": "Press the bridge button now...",
        "enter_ip": "Enter the bridge IP first.",
        "waiting": "Waiting for button press... {s} s",
        "pair_fail": "Failed: {msg}", "unreachable": "bridge unreachable ({e})",
        "pair_timeout": "timed out - button not pressed in time",
        "tray_open": "Open", "tray_refresh": "Refresh",
        "tray_config": "Settings...", "tray_quit": "Quit",
        "tray_tt": "Philips Hue control",
        "brightness": "Brightness", "color": "Color",
        "more_colors": "More colors...", "white": "Whites",
    },
    "fr": {
        "refresh_tt": "Rafraichir", "settings_tt": "Configuration",
        "loading": "Chargement...",
        "add_room": "Piece", "add_zone": "Zone",
        "add_room_tt": "Nouvelle piece - regroupe des appareils "
                       "(une lampe n'est que dans une seule piece)",
        "add_zone_tt": "Nouvelle zone - regroupe des lampes librement "
                       "(les zones peuvent se chevaucher)",
        "badge_room": "PIECE", "badge_zone": "ZONE",
        "edit_btn": "Editer", "delete_btn": "Supprimer",
        "scenes": "Scenes", "lights": "Lumieres", "all_group": "Tout le groupe",
        "others": "Autres", "other_scenes": "Autres scenes",
        "new_scene_tt": "Nouvelle scene dans ce groupe",
        "scene_activated": "Scene : {name}", "vide": "vide",
        "tile_lamps": "{n} lampe(s)", "scene_empty": " (scene vide)",
        "menu_activate": "Activer", "menu_edit": "Editer...",
        "menu_delete": "Supprimer...", "toggle_tt": "Allumer / eteindre",
        "title_new_scene": "Nouvelle scene", "title_edit_scene": "Editer la scene",
        "name": "Nom", "room_zone": "Piece / zone",
        "capture_new": "Capturer l'etat actuel des lampes",
        "capture_edit": "Remplacer les couleurs par l'etat actuel des lampes",
        "editor_tip": "Regle d'abord tes lampes (couleurs, luminosite), "
                      "puis la scene memorise cet etat.",
        "cancel": "Annuler", "save": "Enregistrer", "scene_default": "Scene",
        "del_scene_title": "Supprimer la scene",
        "del_scene_msg": "Supprimer '{name}' ? Cette action est definitive.",
        "no_lamp_group": "Ce groupe ne contient aucune lampe.",
        "saving": "Enregistrement...", "deleting": "Suppression...",
        "title_new_zone": "Nouvelle zone", "title_edit_zone": "Editer la zone",
        "title_new_room": "Nouvelle piece", "title_edit_room": "Editer la piece",
        "zone_lights": "Lampes de cette zone",
        "room_devices": "Appareils de cette piece",
        "zone_hint": "Une zone regroupe des lampes de plusieurs pieces. Les zones "
                     "peuvent se chevaucher et une lampe peut etre dans plusieurs.",
        "room_hint": "Une piece reflete l'installation physique et contient des "
                     "appareils. Une lampe n'appartient qu'a une seule piece.",
        "member_in_room": "{name}  - dans {room}",
        "no_members": "Rien de disponible ici.",
        "del_zone_title": "Supprimer la zone",
        "del_zone_msg": "Supprimer la zone '{name}' ?",
        "del_room_title": "Supprimer la piece",
        "del_room_msg": "Supprimer la piece '{name}' ? Les lampes restent, "
                        "elles quittent seulement cette piece.",
        "room_default": "Piece", "zone_default": "Zone",
        "settings_title": "Configuration", "bridge_hdr": "Pont Philips Hue",
        "ip_info": "Adresse IP du pont. Modifie-la si le pont a change d'IP "
                   "(la cle d'acces reste valide pour le meme pont).",
        "repair_btn": "Changer de pont / re-appairer...",
        "disconnect_btn": "Se deconnecter de ce pont",
        "disconnect_title": "Se deconnecter",
        "disconnect_msg": "Oublier ce pont et ses cles ? Il faudra re-appairer.",
        "close": "Fermer", "appearance_hdr": "Apparence",
        "columns_label": "Tuiles par ligne", "language_label": "Langue",
        "start_min_label": "Demarrer reduit dans le tray",
        "setup_title": "Appairage du pont Hue",
        "setup_hdr": "Connexion au pont Philips Hue",
        "setup_steps": "1.  Detecte le pont (ou saisis son IP).\n"
                       "2.  Appuie sur le gros bouton rond du pont.\n"
                       "3.  Clique sur 'Appairer' dans les 30 secondes.",
        "detect": "Detecter", "pair": "Appairer",
        "searching": "Recherche du pont sur le reseau...",
        "detect_fail": "Detection auto impossible - saisis l'IP a la main.",
        "found": "Pont trouve : {ip}.  Appuie sur son bouton puis 'Appairer'.",
        "none_found": "Aucun pont detecte - saisis l'IP a la main.",
        "press_now": "Appuie sur le bouton du pont maintenant...",
        "enter_ip": "Indique d'abord l'IP du pont.",
        "waiting": "Attente de l'appui sur le bouton... {s} s",
        "pair_fail": "Echec : {msg}", "unreachable": "pont injoignable ({e})",
        "pair_timeout": "delai depasse - bouton non presse a temps",
        "tray_open": "Ouvrir", "tray_refresh": "Rafraichir",
        "tray_config": "Configuration...", "tray_quit": "Quitter",
        "tray_tt": "Controle Philips Hue",
        "brightness": "Luminosite", "color": "Couleur",
        "more_colors": "Plus de couleurs...", "white": "Blancs",
    },
}

LANG = "en"


def set_lang(code):
    global LANG
    LANG = code if code in STRINGS else "en"


def t(key, **kw):
    d = STRINGS.get(LANG, STRINGS["en"])
    s = d.get(key) or STRINGS["en"].get(key, key)
    return s.format(**kw) if kw else s
