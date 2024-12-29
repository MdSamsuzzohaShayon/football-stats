from enum import Enum


# Define the Enum for Match Status
class MatchStatus(str, Enum):
    NOT_STARTED = "not_started"
    RUNNING = "running"
    HALF_TIME = "half_time"
    FULL_TIME = "full_time"


# Goalkeeper.
# Defenders,Centre-Back, Sweeper (SW), Left-Back (LB), Right-Back (RB), Wing-Back (LWB/RWB)
# Defensive Midfielder, Central Midfielder (CM), Attacking Midfielder (CAM), Left Midfielder (LM), Right Midfielder (RM), Winger (LW/RW)
# Striker (ST), Centre-Forward (CF), Second Striker (SS), False Nine, Left Forward (LF), Right Forward (RF)
# Playmaker, Target Man, Box-to-Box Midfielder, Inverted Winger, Libero
# Define the Enum for Football Positions
class PlayerPosition(str, Enum):
    # Goalkeeper
    GOALKEEPER = "goalkeeper"

    # Defenders
    CENTRE_BACK = "centre_back" # Used
    SWEEPER = "sweeper"
    LEFT_BACK = "left_back" # Used
    RIGHT_BACK = "right_back" # Used
    LEFT_WING_BACK = "left_wing_back"
    RIGHT_WING_BACK = "right_wing_back"

    # Midfielders
    DEFENSIVE_MIDFIELDER = "defensive_midfielder" # Used
    CENTRAL_MIDFIELDER = "central_midfielder" # used
    ATTACKING_MIDFIELDER = "attacking_midfielder" # Used
    LEFT_MIDFIELDER = "left_midfielder"
    RIGHT_MIDFIELDER = "right_midfielder"
    LEFT_WINGER = "left_winger" # Used
    RIGHT_WINGER = "right_winger"

    # Forwards
    STRIKER = "striker" # used
    CENTRE_FORWARD = "centre_forward" # Used
    SECOND_STRIKER = "second_striker"
    FALSE_NINE = "false_nine"
    LEFT_FORWARD = "left_forward"
    RIGHT_FORWARD = "right_forward"

    # Specialized Roles
    PLAYMAKER = "playmaker"
    TARGET_MAN = "target_man"
    BOX_TO_BOX_MIDFIELDER = "box_to_box_midfielder"
    INVERTED_WINGER = "inverted_winger"
    LIBERO = "libero"
