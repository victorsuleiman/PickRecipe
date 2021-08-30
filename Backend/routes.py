from flask import Flask, render_template,  request, escape, redirect
from flask_socketio import SocketIO, emit
from flask_pymongo import PyMongo
from bson.json_util import dumps, loads 


app = Flask(__name__)
app.config['SECRET_KEY'] = 'someSecretKey123'
app.config['DEBUG'] = True

socketio = SocketIO(app)
users = {}

app.config["MONGO_URI"] = "mongodb+srv://admin:admin@cluster0.usuw1.mongodb.net/PickYourRecipe?retryWrites=true&w=majority" # replace the URI with your own connection
mongo = PyMongo(app)


@app.route('/')
def init():                            # this is a comment. You can create your own function name
    return render_template('registration.html')
    
@socketio.on('register')
def register(data) :
    print(data)
    username = data['username']
    password = data['password']
    
    user = {'username':username, 'password':password, 'pantry':[],'favorites':[]}
    
    mongo.db.users.insert_one(user)
    
    emit('notification', 'username {} successfully registered'.format(username))
    
@socketio.on('fetchUsername')
def fetchUsername(data) :
    username = data['username']
    print("Looking for username {} to register".format(username))
    usernameToFind = mongo.db.users.find_one({'username':username})
    
    if usernameToFind == None:
        print("Username not found.")
        emit('usernameSearchResult',False)
    else:
        print("Username found.")
        emit('usernameSearchResult',True)
        

@socketio.on('fetchUsernameForLogin')
def fetchUsernameForLogin(data):
    username = data['username']
    print("Looking for username {} to login".format(username))
    usernameToFind = mongo.db.users.find_one({'username':username})
    json_data = dumps(usernameToFind)
    emit('usernameSearchForLogin', json_data)
    

@socketio.on('addIngredientToPantry')
def addIngredientToPantry(data):
    username = data['username']
    ingredient = data['ingredient']
    mongo.db.users.update_one(
        {"username":username},
        {
            "$push": { "pantry": ingredient } 
        }
    )
    print("Adding ingredient {} for username {} ".format(ingredient,username))
    emit('onAddIngredient',ingredient)
    
@socketio.on('removeIngredient')
def deleteIngredient(data):
    username = data['username']
    ingredient = data['ingredient']
    mongo.db.users.update_one(
        {"username":username},
        {
            "$pull": { "pantry": ingredient } 
        }
    )
    print("Removing ingredient {} for username {} ".format(ingredient,username))
    emit('onRemoveIngredient',ingredient)
    
@socketio.on('getRecipes')
def getRecipes():
    recipes = list(mongo.db.recipes.find({}))
    json_recipes = dumps(recipes)
    emit('onGetRecipes',json_recipes)
    
@socketio.on('addComment')
def addComment(data):
    comment = data['comment']
    recipeId = data['id']
    mongo.db.recipes.update_one(
        {"id":recipeId},
        {
            "$push": { "comments": comment } 
        }
    )
    print("Adding comment {} for recipeId {} ".format(comment,recipeId))
    emit('onAddComment')
    
@socketio.on('updateRating')
def updateRating(data):
    rating = float(data['rating'])
    recipeId = data['id']
    mongo.db.recipes.update_one(
    {"id":recipeId},
        {
            "$set": { "rating": rating } 
        }
    )
    print("Updated rating to {} for recipeId {} ".format(rating,recipeId))
    
@socketio.on('getRecipe')
def checkPantryMatch(data):
    recipeId = data['id']
    print("Checking pantry match for recipeId {} ".format(recipeId))
    recipe = mongo.db.recipes.find_one({'id':recipeId})
    json_data = dumps(recipe)
    emit('onGetRecipe',json_data)
    
@socketio.on('addFavorite')
def addFavorite(data):
    username = data['username']
    recipeId = data['id']
    print("Adding recipeId {} as favorite for username {} ".format(recipeId,username))
    mongo.db.users.update_one(
        {"username":username},
        {
            "$push": { "favorites": recipeId } 
        }
    )
    emit('onAddFavorite')
    
@socketio.on('removeFavorite')
def removeFavorite(data):
    username = data['username']
    recipeId = data['id']
    print("Removing recipeId {} from favorites for username {} ".format(recipeId,username))
    mongo.db.users.update_one(
        {"username":username},
        {
            "$pull": { "favorites": recipeId } 
        }
    )
    emit('onRemoveFavorite')


if __name__ == '__main__':
    socketio.run(app,host = '0.0.0.0')