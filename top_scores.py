# Top Scores: catch the star as often as you can in 10 seconds. Every game is written into a database, and the best five are shown.
# Use: click or tap the star. When the time is up, click anywhere to play again.
# Try changing: 5, how many games the table shows; 10, the seconds in a game; "scores", the name of the database.
#
# Run it:   pyctures run top_scores.py

db = open_database("scores")        # the file scores.db, made the first time
db.run("create table if not exists games (points, played)")

def best_games():
    return db.query("select points, played from games order by points desc, played desc limit 5")

top = best_games()                  # a list of rows, each a dictionary: {"points": 7, "played": "..."}
score = 0
left = 10                           # seconds left in this game
star = Sprite("⭐", 200, 160, size=60)

def update(dt):
    global left, top
    if left <= 0:                   # the game is over
        return
    left -= dt
    if left <= 0:                   # write this game down, then read the table again
        db.run("insert into games values (?, datetime('now', 'localtime'))", score)
        top = best_games()

def on_mouse_down(x, y):
    global score, left
    if left <= 0:                   # start the next game
        score = 0
        left = 10
    elif star.contains(x, y):
        score += 1
        star.x = random(40, width - 40)
        star.y = random(90, height - 40)

def draw():
    background("midnightblue")
    text(f"Score {score}", 16, 34, "white", 22, "left")
    if left > 0:
        star.draw()
        text(round(left), width / 2, 26, "white", 22, "centre")
        return
    text("Top scores", width / 2, 90, "gold", 28, "centre")
    y = 130
    for place, game in enumerate(top, 1):
        text(f"{place}.   {game['points']} stars   {game['played']}", width / 2, y, "white", 18, "centre")
        y += 30
    text("Click to play again", width / 2, y + 20, "lightskyblue", 18, "centre")
