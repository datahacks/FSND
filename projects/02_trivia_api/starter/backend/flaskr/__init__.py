import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, db, Question, Category

QUESTIONS_PER_PAGE = 10

# Helper functions
def paginate_questions(request, selection):
  page = request.args.get('page', 1, type=int)
  start = (page - 1) * QUESTIONS_PER_PAGE
  end = start + QUESTIONS_PER_PAGE

  questions = [q.format() for q in selection]
  current_questions = questions[start:end]
  return current_questions

def get_quiz_question(selection, previous_questions):
  selection_ids = [s.id for s in selection]
  diff = list(set(selection_ids) - set(previous_questions))
  question = None
  if diff and len(diff) > 1:
    question = Question.query.get(random.choice(diff)).format()
  elif len(diff) == 1:
    question = Question.query.get(diff[0]).format()
  else:
    question = None
  return question

def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)
 
  '''
  Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
  '''
  cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

  '''
  Use the after_request decorator to set Access-Control-Allow
  '''
  @app.after_request
  def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PATCH, DELETE, OPTIONS')
    return response

  ''' 
  Create an endpoint to handle GET requests 
  for all available categories.
  '''
  @app.route('/categories')
  def get_categories():
    categories = Category.query.all()
    #formatted_categories = [c.format() for c in categories]
    if len(categories) == 0:
      abort(404)

    return jsonify({
      'success': True,
      'categories': {c.id:c.type for c in categories}
    })

  ''' 
  Create an endpoint to handle GET requests for questions, 
  including pagination (every 10 questions). 
  This endpoint should return a list of questions, 
  number of total questions, current category, categories. 

  TEST: At this point, when you start the application
  you should see questions and categories generated,
  ten questions per page and pagination at the bottom of the screen for three pages.
  Clicking on the page numbers should update the questions. 
  '''
  @app.route('/questions')
  def get_questions():
    questions = Question.query.order_by(Question.id).all()
    current_questions = paginate_questions(request, questions)
    
    categories = Category.query.all()

    if(len(current_questions) == 0) or (len(categories) == 0):
      abort(404)

    return jsonify ({
      'questions': current_questions,
      'total_questions': len(questions),
      'current_category': None,
      'categories': {c.id:c.type for c in categories},
      'success': True
    })

  '''
  Create an endpoint to DELETE question using a question ID. 

  TEST: When you click the trash icon next to a question, the question will be removed.
  This removal will persist in the database and when you refresh the page. 
  '''
  @app.route('/questions/<int:question_id>', methods = ['DELETE'])
  def delete_question(question_id):
    try:
      question = Question.query.filter(Question.id == question_id).one_or_none()
      if question is None:
        abort(404)
      
      question.delete()
      selection = Question.query.order_by(Question.id).all()
      current_questions = paginate_questions(request, selection)

      return jsonify({
        'success': True,
        'deleted': question_id,
        'questions': current_questions,
        'total_questions': len(Question.query.all())
      })
    except:
      abort(422)
    finally:
      db.session.close()
    
  '''
  Create an endpoint to POST a new question, 
  which will require the question and answer text, 
  category, and difficulty score.

  TEST: When you submit a question on the "Add" tab, 
  the form will clear and the question will appear at the end of the last page
  of the questions list in the "List" tab.  
  '''
  @app.route('/questions', methods = ['POST'])
  def create_question():
    body = request.get_json()

    new_question = body.get('question',None)
    answer = body.get('answer', None)
    difficulty = body.get('difficulty', None)
    category = body.get('category', None)

    try:
      question = Question(question = new_question, answer = answer, category = category, difficulty = difficulty)
      question.insert()

      selection = Question.query.order_by(Question.id).all()
      current_questions = paginate_questions(request, selection)

      return jsonify({
        'success': True,
        'created': question.id,
        'questions': current_questions,
        'total_questions': len(Question.query.all())
      })
    except:
      abort(422)
    finally:
      db.session.close()

  ''' 
  Create a POST endpoint to get questions based on a search term. 
  It should return any questions for whom the search term 
  is a substring of the question. 

  TEST: Search by any phrase. The questions list will update to include 
  only question that include that string within their question. 
  Try using the word "title" to start. 
  '''
  @app.route('/questions/search', methods = ['POST'])
  def search_questions():
    body = request.get_json()

    searchTerm = body.get('searchTerm', None)
    try:
      selection = Question.query.filter(Question.question.ilike('%' + searchTerm + '%')).all()
      current_questions = paginate_questions(request, selection)

      return jsonify({
        'success': True,
        'questions': current_questions,
        'total_questions': len(current_questions)
        })
    except:
      abort(422)
  
  ''' 
  Create a GET endpoint to get questions based on category. 

  TEST: In the "List" tab / main screen, clicking on one of the 
  categories in the left column will cause only questions of that 
  category to be shown. 
  '''
  @app.route('/categories/<int:category_id>/questions', methods = ['GET'])
  def get_questions_by_category(category_id):
    valid_categories = [c.id for c in Category.query.all()]
    if category_id not in valid_categories:
      abort(404)
    selection = Question.query.filter(Question.category == category_id).all()
    current_questions = paginate_questions(request, selection)

    return jsonify({
      'success': True,
      'questions': current_questions,
      'total_questions': len(current_questions)
    })
  
  '''
  Create a POST endpoint to get questions to play the quiz. 
  This endpoint should take category and previous question parameters 
  and return a random questions within the given category, 
  if provided, and that is not one of the previous questions. 

  TEST: In the "Play" tab, after a user selects "All" or a category,
  one question at a time is displayed, the user is allowed to answer
  and shown whether they were correct or not. 
  '''
  @app.route('/quizzes', methods = ['POST'])
  def quizzes():
    body = request.get_json()
    previous_questions = body.get('previous_questions', [])
    quiz_category_id = int(body.get('quiz_category', {}).get('id', 0))

    all_category_ids = [c.id for c in Category.query.all()]

    if (quiz_category_id in all_category_ids):
      selection = Question.query.filter(Question.category == quiz_category_id).all()
    else:
      selection = Question.query.all()

    if selection is None:
      abort(404)

    question = get_quiz_question(selection, previous_questions)

    return jsonify({
      'success': True,
      'question': question
      })

  ''' 
  Create error handlers for all expected errors 
  including 404 and 422. 
  '''
  @app.errorhandler(404)
  def not_found(error):
    return jsonify({
      'success': False,
      'error': '404',
      'message': 'Resource Not Found'
    }), 404

  @app.errorhandler(422)
  def unprocessable_request(error):
    return jsonify({
      'success': False,
      'error': '422',
      'message': 'Not able to process request message'
    }), 422

  @app.errorhandler(400)
  def bad_request(error):
    return jsonify({
      'success': False,
      'error': '400',
      'message': 'Bad Request'
    }), 400

  @app.errorhandler(405)
  def method_not_allowed(error):
    return jsonify({
      'success': False,
      'error': '405',
      'message': 'Method Not Allowed'
    }), 405

  return app

    