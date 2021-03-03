import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category


def paginate_questions(request):
    items_limit = request.args.get('limit', 10, type=int)
    selected_page = request.args.get('page', 1, type=int)
    current_index = selected_page - 1
    body = request.get_json()

    if body:
        search = body.get('search')
        if search:
            questions = Question.query.filter(
                          Question.question.ilike(
                              '%{}%'.format(search))).limit(
                                items_limit).offset(
                                    current_index * items_limit).all()
        else:
            questions = Question.query.order_by(
                          Question.id
                        ).limit(items_limit).offset(
                            current_index * items_limit).all()
    else:
        questions = Question.query.order_by(
                          Question.id
                        ).limit(items_limit).offset(
                            current_index * items_limit).all()
    new_list = [q.format() for q in questions]
    current_questions = new_list

    return current_questions


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    CORS(app, resources={r"/": {"origins": "*"}})

    @app.after_request
    def after_request(response):
        response.headers.add(
            'Access-Control-Allow-Headers',
            'Content-Type,Authorization,true')
        response.headers.add(
            'Access-Control-Allow-Methods',
            'GET,PUT,POST,DELETE,OPTIONS')
        return response

    @app.route('/categories')
    def retrieve_categories():
        selection = Category.query.all()
        categories = [category.format() for category in selection]

        if len(categories) == 0:
            abort(404)
        else:
            return jsonify({
                'success': True,
                'categories': categories,
                'total_categories': len(Category.query.all())
            }), 200

    @app.route('/questions')
    def retrieve_questions():
        current_questions = paginate_questions(request)

        if len(current_questions) == 0:
            abort(404)
        else:
            return jsonify({
                'success': True,
                'questions': current_questions,
                'total_questions': len(Question.query.all())
            })

    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        try:
            question = Question.query.filter(
                Question.id == question_id).one_or_none()

            if question is None:
                abort(404)

            question.delete()
            current_questions = paginate_questions(request)
            return jsonify({
                'success': True,
                'deleted': question_id,
                'questions': current_questions,
                'total_questions': len(Question.query.all())
            })

        except BaseException:
            abort(422)

    @app.route('/questions', methods=['POST'])
    def create_question():
        body = request.get_json()

        new_question = body.get('question', None)
        new_answer = body.get('answer', None)
        new_category = body.get('category', None)
        new_difficulty = body.get('difficulty', None)
        search = body.get('search', None)

        try:
            if search:
                selection = Question.query.filter(
                    Question.question.ilike(
                        '%{}%'.format(search))).all()
                current_questions = paginate_questions(request)

                return jsonify({
                    'success': True,
                    'questions': current_questions,
                    'total_questions': len(selection)
                })

            else:
                if None in (
                        new_answer,
                        new_category,
                        new_difficulty,
                        new_question):
                    abort(422)

                question = Question(
                    question=new_question,
                    answer=new_answer,
                    category=new_category,
                    difficulty=new_difficulty)
                question.insert()

                current_questions = paginate_questions(request)
                return jsonify({
                    'success': True,
                    'created': question.id,
                    'questions': current_questions,
                    'total_questions': len(Question.query.all())
                }), 201

        except BaseException:
            abort(422)

    @app.route('/categories/<int:category_id>/questions')
    def get_questions_from_a_category(category_id):
        items_limit = request.args.get('limit', 10, type=int)
        selected_page = request.args.get('page', 1, type=int)
        current_index = selected_page - 1
        category = Category.query.filter(
            Category.id == category_id).one_or_none()

        if category is None:
            abort(404)

        selection = Question.query.filter(
            Question.category == category_id).all()

        current_questions = Question.query.filter(
                              Question.category == category_id
                            ).limit(items_limit).offset(
                                current_index * items_limit).all()

        new_list = [q.format() for q in current_questions]
        return jsonify({
            'success': True,
            'questions': new_list,
            'category': category_id,
            'total_questions': len(selection)
        })

    @app.route('/quizzes', methods=['POST'])
    def play_quiz():
        body = request.get_json()
        previous_questions = body.get('previous_questions', [])
        quiz_category = body.get('quiz_category', None)

        if quiz_category is None:
            abort(404)

        if quiz_category['id'] == 0:
            questions = Question.query.all()
        else:
            questions = Question.query.filter(
                Question.category == quiz_category['id']).all()

        next_question = True
        random_question = random.choice(questions).format()

        while next_question:
            if random_question['id'] not in previous_questions:
                next_question = False
            else:
                random_question = random.choice(questions).format()

        return jsonify({
            'success': True,
            'question': random_question
        }), 200

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": "resource not found"
        }), 404

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "unprocessable"
        }), 422

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False,
            "error": 400,
            "message": "bad request"
        }), 400

    @app.errorhandler(405)
    def bad_request(error):
        return jsonify({
            "success": False,
            "error": 405,
            "message": "method not allowed"
        }), 405

    return app
