import argparse
import datetime
import os
import random
import subprocess

import chess
import chess.engine
import chess.pgn


def main():
    parser = argparse.ArgumentParser(
        prog="tbc", description="Play Maia from your terminal"
    )
    parser.add_argument(
        "-e",
        "--elo",
        default="1500",
        help="The Elo that Maia will aim to emulate (default: 1500)",
        type=int,
    )
    parser.add_argument(
        "-f",
        "--fen",
        help="Initial position in FEN",
    )
    parser.add_argument(
        "-c",
        "--colour",
        help="Colour to play as (default: random)",
        choices=["w", "b"],
    )
    args = parser.parse_args()

    match args.colour:
        case "w":
            player_colour = chess.WHITE
        case "b":
            player_colour = chess.BLACK
        case _:
            player_colour = random.choice([chess.WHITE, chess.BLACK])

    if args.fen:
        board = chess.Board(args.fen)
    else:
        board = chess.Board()

    model = "maia3-79m"

    with chess.engine.SimpleEngine.popen_uci(
        [
            "maia3-uci",
            "--model",
            model,
            "--use-uci-history",
            "--elo",
            str(args.elo),
        ],
        stderr=subprocess.DEVNULL,
    ) as engine:
        while not board.is_game_over():
            if board.turn is chess.WHITE:
                print(f"{board.fullmove_number:3d}. ", end="")
            else:
                print("     ", end="")
            if board.turn is player_colour:
                while True:
                    cmd = input()
                    if cmd.startswith("!"):
                        match cmd:
                            case "!board":
                                print(board)
                            case "!fen":
                                print(board.fen())
                            case _:
                                print("unknown command")
                        print("     ", end="")
                        continue

                    try:
                        move = board.parse_san(cmd)
                        break
                    except chess.InvalidMoveError:
                        print("invalid move\n     ", end="")
                    except chess.IllegalMoveError:
                        print("illegal move\n     ", end="")
                    except chess.AmbiguousMoveError:
                        print("ambiguous move\n     ", end="")
            else:
                result = engine.play(board, limit=chess.engine.Limit(nodes=1))
                if result.move is None:
                    break
                move = result.move
                print(board.san(move))

            board.push(move)

    game = chess.pgn.Game.from_board(board)
    game.headers["Event"] = "tbc practice game"
    game.headers["Site"] = "local"
    game.headers["Date"] = datetime.datetime.strftime(
        datetime.datetime.today(),  # noqa: DTZ002
        "%Y.%m.%d",
    )
    if player_colour is chess.WHITE:
        game.headers["White"] = os.environ["USER"]
        game.headers["Black"] = f"{model} {args.elo} Elo"
    else:
        game.headers["White"] = f"{model} {args.elo} Elo"
        game.headers["Black"] = os.environ["USER"]
    print(f"\n{game}\n")
