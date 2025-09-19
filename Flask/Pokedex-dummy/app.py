from flask import Flask, render_template, request, redirect, url_for, jsonify
import requests
import json

app = Flask(__name__, template_folder="templates")

# PokeAPI base URL
POKE_API_BASE_URL = "https://pokeapi.co/api/v2"

# Pokemon type colors
TYPE_COLORS = {
    'normal': '#A8A878',
    'fire': '#F08030',
    'water': '#6890F0',
    'electric': '#F8D030',
    'grass': '#78C850',
    'ice': '#98D8D8',
    'fighting': '#C03028',
    'poison': '#A040A0',
    'ground': '#E0C068',
    'flying': '#A890F0',
    'psychic': '#F85888',
    'bug': '#A8B820',
    'rock': '#B8A038',
    'ghost': '#705898',
    'dragon': '#7038F8',
    'dark': '#705848',
    'steel': '#B8B8D0',
    'fairy': '#EE99AC'
}

def get_pokemon_data(pokemon_id):
    """Fetch Pokemon data from PokeAPI"""
    try:
        response = requests.get(f"{POKE_API_BASE_URL}/pokemon/{pokemon_id}")
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"Error fetching Pokemon data: {e}")
        return None

def get_pokemon_by_type(type_name):
    """Fetch Pokemon of a specific type"""
    try:
        response = requests.get(f"{POKE_API_BASE_URL}/type/{type_name}")
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"Error fetching Pokemon type data: {e}")
        return None

@app.route("/")
def index():
    # Fetch some initial Pokemon data for the slideshow
    pokemon_data = []
    # Fetch first 5 Pokemon for the slideshow
    for i in range(1, 6):
        pokemon = get_pokemon_data(i)
        if pokemon:
            pokemon_data.append({
                'id': pokemon['id'],
                'name': pokemon['name'],
                'image': pokemon['sprites']['front_default'],
                'types': [t['type']['name'] for t in pokemon['types']]
            })
    return render_template("index.html", pokemon_data=pokemon_data, type_colors=TYPE_COLORS)

@app.route("/types")
def types():
    return render_template("types.html", type_colors=TYPE_COLORS)

@app.route("/search")
def search():
    return render_template("search.html", type_colors=TYPE_COLORS)

@app.route("/pokemon/<int:pokemon_id>")
def get_pokemon(pokemon_id):
    """API endpoint to get Pokemon data"""
    pokemon = get_pokemon_data(pokemon_id)
    if pokemon:
        return jsonify({
            'id': pokemon['id'],
            'name': pokemon['name'],
            'image': pokemon['sprites']['front_default'],
            'types': [t['type']['name'] for t in pokemon['types']],
            'height': pokemon['height'],
            'weight': pokemon['weight'],
            'abilities': [a['ability']['name'] for a in pokemon['abilities']],
            'stats': {
                stat['stat']['name']: stat['base_stat']
                for stat in pokemon['stats']
            }
        })
    return jsonify({'error': 'Pokemon not found'}), 404

@app.route("/type/<type_name>")
def get_pokemon_by_type_route(type_name):
    """API endpoint to get Pokemon of a specific type"""
    type_data = get_pokemon_by_type(type_name)
    if type_data:
        pokemon_list = []
        for pokemon in type_data['pokemon'][:10]:  # Limit to first 10 Pokemon
            pokemon_id = pokemon['pokemon']['url'].split('/')[-2]
            pokemon_data = get_pokemon_data(pokemon_id)
            if pokemon_data:
                pokemon_list.append({
                    'id': pokemon_data['id'],
                    'name': pokemon_data['name'],
                    'image': pokemon_data['sprites']['front_default'],
                    'types': [t['type']['name'] for t in pokemon_data['types']]
                })
        return jsonify(pokemon_list)
    return jsonify({'error': 'Type not found'}), 404

if __name__ == "__main__":
    app.run(debug=True)