from math import exp
import json

from aqt import mw, qconnect
from aqt.qt import QDialog
from aqt.utils import showWarning
from PyQt6.QtGui import QPixmap, QPainter, QIcon
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QScrollArea
from PyQt6.QtWidgets import QDialog, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QLineEdit, QWidget, QMessageBox

from ..pyobj.attack_dialog import AttackDialog
from ..pyobj.pokemon_trade import PokemonTrade
from ..pyobj.error_handler import show_warning_with_traceback
from ..pyobj.pokemon_obj import PokemonObject
from ..pyobj.InfoLogger import ShowInfoLogger
from ..functions.pokedex_functions import get_pokemon_diff_lang_name, get_pokemon_descriptions, get_all_pokemon_moves, find_details_move, search_pokedex_by_id
from ..functions.pokemon_functions import find_experience_for_level
from ..functions.gui_functions import type_icon_path, move_category_path
from ..functions.sprite_functions import get_sprite_path
from ..gui_entities import MovieSplashLabel
from ..business import split_string_by_length
from ..utils import format_move_name, load_custom_font
from ..resources import icon_path, addon_dir, mainpokemon_path, mypokemon_path, pokemon_tm_learnset_path, itembag_path
from ..texts import attack_details_window_template, attack_details_window_template_end, remember_attack_details_window_template, remember_attack_details_window_template_end

def PokemonCollectionDetails(name, level, id, shiny, ability, type, detail_stats, attacks, base_experience, growth_rate, ev, iv, gender, nickname, individual_id, pokemon_defeated, everstone, captured_date, language, gif_in_collection, remove_levelcap, logger, refresh_callback,form_name):
    # Create a layout for the details panel
    try:
        lang_name = get_pokemon_diff_lang_name(int(id), language).capitalize()
        lang_desc = get_pokemon_descriptions(int(id), language)
        description = lang_desc
        layout = QVBoxLayout()
        typelayout = QHBoxLayout()
        attackslayout = QVBoxLayout()
        # Display the Pokémon image
        pkmnimage_label = QLabel()
        pkmnpixmap = QPixmap()
        pkmnimage_path = get_sprite_path("front", "gif" if gif_in_collection else "png", id, shiny, gender, form_name=form_name)

        if gif_in_collection:
            pkmnimage_label = MovieSplashLabel(pkmnimage_path)
        else:
            pkmnpixmap.load(str(pkmnimage_path))
            max_width = 150
            original_width = pkmnpixmap.width()
            original_height = pkmnpixmap.height()
            new_width = max_width
            new_height = (original_height * max_width) // original_width
            pkmnpixmap = pkmnpixmap.scaled(new_width, new_height)
            pkmnimage_label.setPixmap(pkmnpixmap)
        typeimage_file = f"{type[0]}.png"
        typeimage_path = addon_dir / "addon_sprites" / "Types" / typeimage_file
        pkmntype_label = QLabel()
        pkmntypepixmap = QPixmap()
        pkmntypepixmap.load(str(typeimage_path))
        if len(type) > 1:
            type_image_file2 = f"{type[1]}.png"
            typeimage_path2 = addon_dir / "addon_sprites" / "Types" / type_image_file2
            pkmntype_label2 = QLabel()
            pkmntypepixmap2 = QPixmap()
            pkmntypepixmap2.load(str(typeimage_path2))
        
        # Custom font
        custom_font = load_custom_font(int(20), language)
        namefont = load_custom_font(int(30), language)
        namefont.setUnderline(True)

        if nickname is None:
            capitalized_name = f"{lang_name.capitalize()} {' ⭐ ' if shiny else ''}"
        else:
            capitalized_name = f"{nickname} {' ⭐ ' if shiny else ''} ({lang_name.capitalize()})"
        if (
            language == 11
            or language == 12
            or language == 4
            or language == 3
            or language == 2
            or language == 1
        ):
            result = list(split_string_by_length(description, 30))
        else:
            result = list(split_string_by_length(description, 55))
        description_formated = '\n'.join(result)
        description_txt = f"Description: \n {description_formated}"
        lvl = f" Level: {level}"
        ability_txt = f" Ability: {ability.capitalize()}"
        type_txt = f" Type:"
        stats_list = []
        for key, val in detail_stats.items():
            if key not in ("hp", "atk", "def", "spa", "spd", "spe"):
                continue
            stat = PokemonObject.calc_stat(key, val, level, iv[key], ev[key], "serious")
            stats_list.append(stat)
        stats_list.append(detail_stats.get("xp", 0))
        stats_txt = f"Stats:\n Hp: {stats_list[0]}\n Attack: {stats_list[1]}\n Defense: {stats_list[2]}\n Special-attack: {stats_list[3]}\n Special-defense: {stats_list[4]}\n Speed: {stats_list[5]}\n XP: {stats_list[6]}"
        attacks_txt = "MOVES:"
        for attack in attacks:
            attacks_txt += f"\n{attack.capitalize()}"

        _stats_dict = {
            "hp": stats_list[0],
            "atk": stats_list[1],
            "def": stats_list[2],
            "spa": stats_list[3],
            "spd": stats_list[4],
            "spe": stats_list[5],
            "xp": stats_list[6]
            }
        CompleteTable_layout = PokemonDetailsStats(_stats_dict, growth_rate, level, remove_levelcap, language)

        if gender == "M":
            gender_symbol = "♂"
        elif gender == "F":
            gender_symbol = "♀"
        elif gender == "N":
            gender_symbol = ""
        else:
            gender_symbol = ""

        name_label = QLabel(f"{capitalized_name} - {gender_symbol}")
        name_label.setFont(namefont)
        description_label = QLabel(description_txt)
        level_label = QLabel(lvl)
        ability_label = QLabel(ability_txt)
        attacks_label = QLabel(attacks_txt)
        pokemon_defeated_label = QLabel(f"Pokemon Defeated: {pokemon_defeated}")
        if captured_date is not None :
            captured_date_label = QLabel(f"Captured: {captured_date.split()[0]}")
        else:
            captured_date_label = QLabel(f"Captured: N/A")

        level_label.setFont(custom_font)
        type_label = QLabel("Type:")
        type_label.setFont(custom_font)
        ability_label.setFont(custom_font)
        attacks_label.setFont(custom_font)
        description_label.setFont(load_custom_font(15 if language != 1 else 20, language))
        pokemon_defeated_label.setFont(custom_font)
        captured_date_label.setFont(custom_font)

        if gif_in_collection is False:
            pkmnimage_label.setFixedHeight(100)
        pkmnimage_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        level_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        type_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignCenter)
        ability_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        attacks_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pokemon_defeated_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        captured_date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        level_label.setFixedWidth(230)
        ability_label.setFixedWidth(230)
        attacks_label.setFixedWidth(230)
        attacks_label.setFixedHeight(70)

        first_layout = QHBoxLayout()
        TopL_layout_Box = QVBoxLayout()
        TopR_layout_Box = QVBoxLayout()
        typelayout_widget = QWidget()
        TopL_layout_Box.addWidget(level_label)
        TopL_layout_Box.addWidget(pkmnimage_label)

        typelayout.addWidget(type_label)
        typelayout.addWidget(pkmntype_label)
        pkmntype_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if len(type) > 1:
            typelayout.addWidget(pkmntype_label2)
            pkmntype_label2.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom)

        typelayout_widget.setLayout(typelayout)
        typelayout_widget.setFixedWidth(230)
        TopL_layout_Box.addWidget(typelayout_widget)
        TopL_layout_Box.addWidget(ability_label)
        TopL_layout_Box.addWidget(captured_date_label)
        TopL_layout_Box.addWidget(pokemon_defeated_label)

        TopR_layout_Box.addWidget(attacks_label)
        attacks_details_button = QPushButton("Attack Details")
        qconnect(attacks_details_button.clicked, lambda: attack_details_window(attacks))
        remember_attacks_details_button = QPushButton("Remember Attacks")
        all_attacks = get_all_pokemon_moves(name, level)
        qconnect(remember_attacks_details_button.clicked, lambda: remember_attack_details_window(id, attacks, all_attacks, logger))
        forget_attacks_details_button = QPushButton("Forget Attacks")
        qconnect(forget_attacks_details_button.clicked, lambda: forget_attack_details_window(id, attacks, logger))

        tm_attacks_details_button = QPushButton("Learn attacks from TMs") 
        qconnect(tm_attacks_details_button.clicked, lambda: tm_attack_details_window(id, attacks, logger))
        
        #free_pokemon_button = QPushButton("Release Pokemon") #add Details to Moves unneeded button
        TopR_layout_Box.addWidget(attacks_label)
        TopR_layout_Box.addWidget(attacks_details_button)
        TopR_layout_Box.addWidget(remember_attacks_details_button)
        TopR_layout_Box.addWidget(forget_attacks_details_button)
        TopR_layout_Box.addWidget(tm_attacks_details_button)
        TopR_layout_Box.addWidget(captured_date_label)
        TopR_layout_Box.addWidget(pokemon_defeated_label)

        first_layout.addLayout(TopL_layout_Box)
        first_layout.addLayout(TopR_layout_Box)

        layout.addWidget(name_label)
        layout.addLayout(first_layout)
        layout.addWidget(description_label)
        statstablelayout = QWidget()
        statstablelayout.setLayout(CompleteTable_layout)
        statstablelayout.setFixedHeight(190)
        layout.addWidget(statstablelayout)

        free_pokemon_button = QPushButton("Release Pokemon")
        qconnect(free_pokemon_button.clicked, lambda: PokemonFree(individual_id, name, logger, refresh_callback))
        trade_pokemon_button = QPushButton("Trade Pokemon")
        qconnect(trade_pokemon_button.clicked, lambda: PokemonTrade(name, id, level, ability, iv, ev, gender, attacks, individual_id, logger, refresh_callback))
        rename_button = QPushButton("Rename Pokemon")
        rename_input = QLineEdit()
        rename_input.setPlaceholderText("Enter a new Nickname for your Pokemon")
        qconnect(rename_button.clicked, lambda: rename_pkmn(rename_input.text(), name, individual_id, logger, refresh_callback))

        layout.addWidget(trade_pokemon_button)
        layout.addWidget(free_pokemon_button)
        layout.addWidget(rename_input)
        layout.addWidget(rename_button)

        return layout  # Return layout instead of showing dialog

    except Exception as e:
        show_warning_with_traceback(exception=e, message="Error occured in Pokemon Details Button:")

        return QVBoxLayout()  # Return empty layout on error


def PokemonDetailsStats(detail_stats, growth_rate, level, remove_levelcap, language):
    CompleteTable_layout = QVBoxLayout()
    # Stat colors
    stat_colors = {
        "hp": QColor(255, 0, 0),  # Red
        "atk": QColor(255, 165, 0),  # Orange
        "def": QColor(255, 255, 0),  # Yellow
        "spa": QColor(0, 0, 255),  # Blue
        "spd": QColor(0, 128, 0),  # Green
        "spe": QColor(255, 192, 203),  # Pink
        "total": QColor(168, 168, 167),  # Beige
        "xp": QColor(58,155,220),  # lightblue
        # Add any other stats that might appear
        "current_hp": QColor(200, 0, 0),  # Darker red
        "max_hp": QColor(255, 0, 0)  # Red
    }

    #custom font
    custom_font = load_custom_font(int(20), language)

    # Populate the table and create the stat bars
    for row, (stat, value) in enumerate(detail_stats.items()):
        # Skip unknown stats that are not in stat_colors
        if stat not in stat_colors:
            continue
            
        stat_item2 = QLabel(stat.capitalize())
        max_width_stat_item = 200
        stat_item2.setFixedWidth(max_width_stat_item)
        value_item2 = QLabel(str(value))
        stat_item2.setFont(custom_font)
        value_item2.setFont(custom_font)
        # Create a bar item
        bar_item2 = QLabel()
        if stat == "xp":
            experience = int(find_experience_for_level(growth_rate, level, True))
            value = int((int(value) / int(experience)) * max_width_stat_item)
        else:
            value = int(max_width_stat_item * (1 - exp(-value / max_width_stat_item)))  # Small function to ensure that the length of the colored bar doesn't exceed max_width_stat_item
        pixmap2 = createStatBar(stat_colors.get(stat), value)
        # Convert the QPixmap to an QIcon
        icon = QIcon(pixmap2)
        # Set the QIcon as the background for the QLabel
        bar_item2.setPixmap(pixmap2)
        layout_row = QHBoxLayout()
        layout_row.addWidget(stat_item2)
        layout_row.addWidget(value_item2)
        layout_row.addWidget(bar_item2)
        stat_item2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bar_item2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        CompleteTable_layout.addLayout(layout_row)

    return CompleteTable_layout

def createStatBar(color, value):
    pixmap = QPixmap(200, 10)
    pixmap.fill(QColor(0, 0, 0, 0))  # RGBA where A (alpha) is 0 for full transparency
    
    # Default to gray if color is None
    if color is None:
        color = QColor(128, 128, 128)  # Gray
    
    painter = QPainter(pixmap)

    # Draw bar in the background
    painter.setPen(QColor(Qt.GlobalColor.black))
    painter.setBrush(QColor(0, 0, 0, 200))  # Semi-transparent black
    painter.drawRect(0, 0, 200, 10)

    # Draw the colored bar based on the value
    painter.setBrush(color)  # Now color is guaranteed to be a valid QColor
    painter.drawRect(0, 0, value, 10)

    painter.end()  # Important: end the painter to avoid memory leaks
    return pixmap

def attack_details_window(attacks):
    window = QDialog()
    window.setWindowIcon(QIcon(str(icon_path)))
    layout = QVBoxLayout()
    # HTML content
    html_content = attack_details_window_template
    # Loop through the list of attacks and add them to the HTML content
    for attack in attacks:
        move = find_details_move(format_move_name(attack))
        if move is None:
            attack = attack.replace(" ", "")
            try:
                move = find_details_move(format_move_name(attack))
            except:
                logger.log_and_showinfo("info",f"Can't find the attack {attack} in the database.")
                move = find_details_move("tackle")
        if move is None:
            continue
        html_content += f"""
        <tr>
          <td class="move-name">{move['name']}</td>
          <td><img src="{type_icon_path(move['type'])}" alt="{move['type']}"/></td>
          <td><img src="{move_category_path(move['category'].lower())}" alt="{move['category']}"/></td>
          <td class="basePower">{move['basePower']}</td>
          <td class="no-accuracy">{move['accuracy']}</td>
          <td>{move['pp']}</td>
          <td>{move['shortDesc']}</td>
        </tr>
        """
    html_content += attack_details_window_template_end

    # Create a QLabel to display the HTML content
    label = QLabel(html_content)
    label.setAlignment(Qt.AlignmentFlag.AlignLeft)  # Align the label's content to the top
    label.setScaledContents(True)  # Enable scaling of the pixmap

    layout.addWidget(label)
    window.setLayout(layout)
    window.exec()

def remember_attack_details_window(id, attack_set, all_attacks, logger):
    window = QDialog()
    window.setWindowIcon(QIcon(str(icon_path)))
    outer_layout = QVBoxLayout(window)
    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)
    content_widget = QWidget()
    layout = QHBoxLayout(content_widget)
    html_content = remember_attack_details_window_template
    for attack in all_attacks:
        move = find_details_move(attack)
        html_content += f"""
        <tr>
          <td class="move-name">{move['name']}</td>
          <td><img src="{type_icon_path(move['type'])}" alt="{move['type']}"/></td>
          <td><img src="{move_category_path(move['category'].lower())}" alt="{move['category']}"/></td>
          <td class="basePower">{move['basePower']}</td>
          <td class="no-accuracy">{move['accuracy']}</td>
          <td>{move['pp']}</td>
          <td>{move['shortDesc']}</td>
        </tr>
        """
    html_content += remember_attack_details_window_template_end
    label = QLabel(html_content)
    label.setAlignment(Qt.AlignmentFlag.AlignLeft)
    label.setScaledContents(True)
    attack_layout = QVBoxLayout()
    for attack in all_attacks:
        remember_attack_button = QPushButton(f"Remember {attack}")
        qconnect(remember_attack_button.clicked, lambda checked, a=attack: remember_attack(id, attack_set, a, logger))
        attack_layout.addWidget(remember_attack_button)
    attack_layout_widget = QWidget()
    attack_layout_widget.setLayout(attack_layout)
    layout.addWidget(label)
    layout.addWidget(attack_layout_widget)
    scroll_area.setWidget(content_widget)
    outer_layout.addWidget(scroll_area)
    window.resize(1000, 400)
    window.exec()

def forget_attack_details_window(id: int, attack_set: list[str], logger: "InfoLogger.ShowInfoLogger") -> None:
    """
    Creates a window that will allow the user to erase moves from a Pokemon.

    Args:
        id (int): The Pokemon's identifier.
        attack_set (list[str]): The Pokemon's move set.
        logger: Logger object that can log info and display windows containing messages.

    Returns:
        None
    """
    window = QDialog()
    window.setWindowIcon(QIcon(str(icon_path)))
    outer_layout = QVBoxLayout(window)
    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)
    content_widget = QWidget()
    layout = QHBoxLayout(content_widget)
    html_content = remember_attack_details_window_template
    for attack in attack_set:
        move = find_details_move(format_move_name(attack))
        if move is None:
            continue
        html_content += f"""
        <tr>
          <td class="move-name">{move['name']}</td>
          <td><img src="{type_icon_path(move['type'])}" alt="{move['type']}"/></td>
          <td><img src="{move_category_path(move['category'].lower())}" alt="{move['category']}"/></td>
          <td class="basePower">{move['basePower']}</td>
          <td class="no-accuracy">{move['accuracy']}</td>
          <td>{move['pp']}</td>
          <td>{move['shortDesc']}</td>
        </tr>
        """
    html_content += remember_attack_details_window_template_end
    label = QLabel(html_content)
    label.setAlignment(Qt.AlignmentFlag.AlignLeft)
    label.setScaledContents(True)
    attack_layout = QVBoxLayout()
    for attack in attack_set:
        forget_attack_button = QPushButton(f"Forget {attack}")
        qconnect(forget_attack_button.clicked, lambda checked, a=attack: forget_attack(id, attack_set, a, logger))
        attack_layout.addWidget(forget_attack_button)
    attack_layout_widget = QWidget()
    attack_layout_widget.setLayout(attack_layout)
    layout.addWidget(label)
    layout.addWidget(attack_layout_widget)
    scroll_area.setWidget(content_widget)
    outer_layout.addWidget(scroll_area)
    window.resize(1000, 400)
    window.exec()

def remember_attack(id, attacks, new_attack, logger):
    if new_attack in attacks:
        logger.log_and_showinfo("warning","Your pokemon already knows this move!")
        return
    if not mainpokemon_path.is_file():
        logger.log_and_showinfo("warning","Missing Mainpokemon Data !")
        return
    with open(mainpokemon_path, "r", encoding="utf-8") as json_file:
        main_pokemon_data = json.load(json_file)
    for mainpkmndata in main_pokemon_data:
        if mainpkmndata["id"] == id:
            mainpokemon_name = mainpkmndata["name"]
            mainpokemon_individual_id = mainpkmndata["individual_id"]
            attacks = mainpkmndata["attacks"]
            if new_attack:
                msg = ""
                msg += f"Your {mainpkmndata['name'].capitalize()} can learn a new attack !"
                if len(attacks) < 4:
                    attacks.append(new_attack)
                    msg += f"\n Your {mainpkmndata['name'].capitalize()} has learned {new_attack} !"
                    logger.log_and_showinfo("info",f"{msg}")
                else:
                    dialog = AttackDialog(attacks, new_attack)
                    if dialog.exec() == QDialog.DialogCode.Accepted:
                        selected_attack = dialog.selected_attack
                        index_to_replace = None
                        for index, attack in enumerate(attacks):
                            if attack == selected_attack:
                                index_to_replace = index
                        if index_to_replace is not None:
                            attacks[index_to_replace] = new_attack
                            logger.log_and_showinfo("info",f"Replaced '{selected_attack}' with '{new_attack}'")
                        else:
                            logger.log_and_showinfo("info",f"{new_attack} will be discarded.")
            mainpkmndata["attacks"] = attacks
            mypkmndata = mainpkmndata
            mainpkmndata = [mainpkmndata]
            with open(str(mainpokemon_path), "w") as json_file:
                json.dump(mainpkmndata, json_file, indent=2)
            with open(str(mypokemon_path), "r", encoding="utf-8") as output_file:
                mypokemondata = json.load(output_file)
            for index, pokemon_data in enumerate(mypokemondata):
                if pokemon_data["individual_id"] == mainpokemon_individual_id:
                    mypokemondata[index] = mypkmndata
                    break
            with open(str(mypokemon_path), "w") as output_file:
                json.dump(mypokemondata, output_file, indent=2)
        else:
            logger.log_and_showinfo("info","Please Select this Pokemon first as Main Pokemon ! \n Only Mainpokemons can re-learn attacks!")

def forget_attack(id: int, attacks: list[str], attack_to_forget: str, logger: ShowInfoLogger) -> None:
    """
    Forgets a Pokemon's move. This is done by erasing the chosen move from the list
    of attacks known by the Pokemon and then saving that new Pokemon data in the main
    Pokemon data file.

    Args:
        id (int): The Pokemon's identifier.
        attacks (list[str]): The Pokemon's move set.
        attack_to_forget (str): Name of the move to forget.
        logger: Logger object that can log info and display windows containing messages.

    Returns:
        None
    """
    if not mainpokemon_path.is_file():
        logger.log_and_showinfo("warning","Missing Mainpokemon Data !")
        return
    with open(mainpokemon_path, "r", encoding="utf-8") as json_file:
        main_pokemon_data = json.load(json_file)
    for mainpkmndata in main_pokemon_data:
        if mainpkmndata["id"] == id:
            mainpokemon_name = mainpkmndata["name"]
            mainpokemon_individual_id = mainpkmndata["individual_id"]
            attacks = mainpkmndata["attacks"]
            if attack_to_forget:
                if attack_to_forget in attacks:
                    if len(attacks) > 1:
                        attacks.remove(attack_to_forget)
                        msg = f"Your {mainpkmndata['name'].capitalize()} forgot {attack_to_forget}."
                        logger.log_and_showinfo("info",f"{msg}")
                    else:  # If we reach here, it means the Pokemon only has 1 move left. We can't allow this move to be forgotten
                        msg = f"Your {mainpkmndata['name'].capitalize()} only knows this move, you can't forget it ! "
                        logger.log_and_showinfo("info",f"{msg}")
                else:
                    msg = f"Your {mainpkmndata['name'].capitalize()} does not know {attack_to_forget}."
                    logger.log_and_showinfo("info",f"{msg}")
            mainpkmndata["attacks"] = attacks
            mypkmndata = mainpkmndata
            mainpkmndata = [mainpkmndata]
            with open(str(mainpokemon_path), "w") as json_file:
                json.dump(mainpkmndata, json_file, indent=2)
            with open(str(mypokemon_path), "r", encoding="utf-8") as output_file:
                mypokemondata = json.load(output_file)
            for index, pokemon_data in enumerate(mypokemondata):
                if pokemon_data["individual_id"] == mainpokemon_individual_id:
                    mypokemondata[index] = mypkmndata
                    break
            with open(str(mypokemon_path), "w") as output_file:
                json.dump(mypokemondata, output_file, indent=2)
        else:
            logger.log_and_showinfo("info","Please Select this Pokemon first as Main Pokemon ! \n Only Mainpokemons can forget attacks!")

def tm_attack_details_window(id: int, current_pokemon_moveset: list[str], logger: ShowInfoLogger) -> None:
    """
    Creates a window that will allow the user to learn TM moves.

    Args:
        id (int): The Pokemon's identifier.
        current_pokemon_moveset (list[str]): The moves that the Pokemon currently knows.
        logger: Logger object that can log info and display windows containing messages.

    Returns:
        None
    """
    window = QDialog()
    window.setWindowIcon(QIcon(str(icon_path)))
    layout = QHBoxLayout()
    window.setWindowTitle("Learn TM Move")  # Optional: Set a window title
    # Outer layout contains everything
    outer_layout = QVBoxLayout(window)

    # Create a scroll area that will contain our main layout
    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)

    # Main widget that contains the content
    content_widget = QWidget()
    layout = QHBoxLayout(content_widget)  # The main layout is now set on this widget

    # HTML content
    html_content = remember_attack_details_window_template
    from pathlib import Path
    with open(pokemon_tm_learnset_path, "r") as f:
        pokemon_tm_learnset = json.load(f)
    
    pokemon_name = search_pokedex_by_id(id)
    tm_learnset = pokemon_tm_learnset.get(pokemon_name, [])  # TMs that can be learnt by the Pokemon
    with open(itembag_path, "r", encoding="utf-8") as json_file:
        itembag_list = json.load(json_file)
    owned_tms = [item["item"] for item in itembag_list if item.get("type") == "TM"]
    attack_set = [tm for tm in tm_learnset if tm in owned_tms]

    # Loop through the list of attacks and add them to the HTML content
    for attack in attack_set:
        move = find_details_move(attack) or find_details_move(
            format_move_name(attack)
        )

        if move is None:
            continue

        html_content += f"""
        <tr>
          <td class="move-name">{move['name']}</td>
          <td><img src="{type_icon_path(move['type'])}" alt="{move['type']}"/></td>
          <td><img src="{move_category_path(move['category'].lower())}" alt="{move['category']}"/></td>
          <td class="basePower">{move['basePower']}</td>
          <td class="no-accuracy">{move['accuracy']}</td>
          <td>{move['pp']}</td>
          <td>{move['shortDesc']}</td>
        </tr>
        """

    html_content += remember_attack_details_window_template_end

    # Create a QLabel to display the HTML content
    label = QLabel(html_content)
    label.setAlignment(Qt.AlignmentFlag.AlignLeft)  # Align the label's content to the top
    label.setScaledContents(True)  # Enable scaling of the pixmap
    attack_layout = QVBoxLayout()
    for attack in attack_set:
        move = find_details_move(attack)
        forget_attack_button = QPushButton(f"Learn {attack}") #add Details to Moves
        forget_attack_button.clicked.connect(lambda checked, a=attack: remember_attack(id, current_pokemon_moveset, a, logger))  # We can use "remember_attack()" because the process is the same
        attack_layout.addWidget(forget_attack_button)
    attack_layout_widget = QWidget()
    attack_layout_widget.setLayout(attack_layout)
    # Add the label and button layout widget to the main layout
    layout.addWidget(label)
    layout.addWidget(attack_layout_widget)

    # Set the main widget with content as the scroll area's widget
    scroll_area.setWidget(content_widget)

    # Add the scroll area to the outer layout
    outer_layout.addWidget(scroll_area)

    window.setLayout(outer_layout)
    window.resize(1000, 400)  # Optional: Set a default size for the window
    window.exec()

def rename_pkmn(nickname, pkmn_name, individual_id, logger, refresh_callback):
    try:
        # Load the captured Pokémon data
        with open(mypokemon_path, "r", encoding="utf-8") as json_file:
            captured_pokemon_data = json.load(json_file)
            pokemon = None

            # Find the Pokémon by individual_id
            for index, pokemon_data in enumerate(captured_pokemon_data):
                if pokemon_data["individual_id"] == individual_id:
                    pokemon = pokemon_data
                    break

            if pokemon is not None:
                # Update the nickname
                pokemon["nickname"] = nickname
                # Reflect the change in the output JSON file
                with open(str(mypokemon_path), "r", encoding="utf-8") as output_file:
                    mypokemondata = json.load(output_file)
                    # Update the specified Pokémon's data
                    for idx, data in enumerate(mypokemondata):
                        if data["individual_id"] == individual_id:
                            mypokemondata[idx] = pokemon
                            break
                # Save the modified data
                with open(str(mypokemon_path), "w") as output_file:
                    json.dump(mypokemondata, output_file, indent=2)
                # Logging and UI update
                logger.log_and_showinfo("info", f"Your {pkmn_name.capitalize()} has been renamed to {nickname}!")
                refresh_callback()
            else:
                showWarning("Pokémon not found.")
    except Exception as e:
        showWarning(f"An error occurred: {e}")

def PokemonFree(individual_id, name, logger, refresh_callback):
    # Confirmation dialog
    reply = QMessageBox.question(
        None, 
        "Confirm Release", 
        f"Are you sure you want to release {name}?", 
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
        QMessageBox.StandardButton.No
    )

    if reply == QMessageBox.StandardButton.No:
        logger.log_and_showinfo("info","Release cancelled.")
        return

    # Check if the Pokémon is in the main Pokémon file
    with open(mainpokemon_path, "r", encoding="utf-8") as file:
        pokemon_data = json.load(file)

    for pokemon in pokemon_data:
        if pokemon["individual_id"] == individual_id:
            logger.log_and_showinfo("info","You can't free your Main Pokémon!")
            return  # Exit the function if it's a Main Pokémon

    # Load Pokémon list from 'mypokemon_path' file
    try:
        with open(mypokemon_path, "r", encoding="utf-8") as file:
            pokemon_list = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        logger.log_and_showinfo("info","Error: Could not load Pokémon data.")
        return

    # Find the position of the Pokémon with the given individual_id
    position = -1
    for idx, pokemon in enumerate(pokemon_list):
        if pokemon.get("individual_id") == individual_id:
            position = idx
            break

    # If the Pokémon was found, remove it from the list
    if position != -1:
        pokemon_list.pop(position)
        with open(mypokemon_path, 'w') as file:
            json.dump(pokemon_list, file, indent=2)
        logger.log_and_showinfo("info",f"{name.capitalize()} has been let free.")
    else:
        logger.log_and_showinfo("info","No Pokémon found with the specified ID.")
    
    refresh_callback()