#!/usr/bin/env python3

from flask import request, session
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from config import app, db, api
from models import User, Recipe

class Signup(Resource):
    def post(self):
        username = request.json.get('username')
        password = request.json.get('password')
        bio = request.json.get('bio')
        image_url = request.json.get('image_url')
        
        if not username:
            return {'error': 'Username is required'}, 422
        
        try:
            user = User(username=username, bio=bio, image_url=image_url)
            user.password_hash = password
            
            db.session.add(user)
            db.session.commit()
            
            session['user_id'] = user.id
            
            return user.to_dict(), 201
        except IntegrityError as e:
            db.session.rollback()
            return {'error': 'Username already exists'}, 422
        except ValueError as e:
            db.session.rollback()
            return {'error': str(e)}, 422

class CheckSession(Resource):
    def get(self):
        user_id = session.get('user_id')
        
        if not user_id:
            return {'error': 'Unauthorized'}, 401
        
        user = User.query.get(user_id)
        
        if user:
            return user.to_dict(), 200
        else:
            return {'error': 'Unauthorized'}, 401

class Login(Resource):
    def post(self):
        username = request.json.get('username')
        password = request.json.get('password')
        
        user = User.query.filter(User.username == username).first()
        
        if user and user.authenticate(password):
            session['user_id'] = user.id
            return user.to_dict(), 200
        else:
            return {'error': 'Invalid credentials'}, 401

class Logout(Resource):
    def delete(self):
        user_id = session.get('user_id')
        
        if not user_id:
            return {'error': 'Unauthorized'}, 401
        
        session.pop('user_id', None)
        return '', 204

class RecipeIndex(Resource):
    def get(self):
        user_id = session.get('user_id')
        
        if not user_id:
            return {'error': 'Unauthorized'}, 401
        
        recipes = Recipe.query.filter(Recipe.user_id == user_id).all()
        return [recipe.to_dict() for recipe in recipes], 200
    
    def post(self):
        user_id = session.get('user_id')
        
        if not user_id:
            return {'error': 'Unauthorized'}, 401
        
        title = request.json.get('title')
        instructions = request.json.get('instructions')
        minutes_to_complete = request.json.get('minutes_to_complete')
        
        try:
            recipe = Recipe(
                title=title,
                instructions=instructions,
                minutes_to_complete=minutes_to_complete,
                user_id=user_id
            )
            
            db.session.add(recipe)
            db.session.commit()
            
            return recipe.to_dict(), 201
        except (IntegrityError, ValueError) as e:
            db.session.rollback()
            return {'error': str(e)}, 422

api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(RecipeIndex, '/recipes', endpoint='recipes')


if __name__ == '__main__':
    app.run(port=5555, debug=True)