#pragma once
#include "hashmap.h"
#include "randutils.h"
#include "scanner.h"
#include "values.h"

struct Result {
	Value val;
	bool  isConstant;

	static Result from(Value v) {
		Result r;
		r.val        = v;
		r.isConstant = false;
		return r;
	}

	static Result fromConstant(Value v) {
		Result r;
		r.val        = v;
		r.isConstant = true;
		return r;
	}
};

struct Engine {
	// parses an expression and returns a representation
	// of its structure
	typedef Value (Engine::*ExpressionRule)(Token ex);

	Scanner                                             scanner;
	Random                                              random;
	HashMap<String *, Value, StringHash, StringEquals>  rules;
	HashMap<String *, Result, StringHash, StringEquals> results;

	Engine() : scanner(NULL, ""), random() {}
	Token consume(TokenType t, const char *message);
	Value parseExpression(Token t);
	Value parseExpression();
	Value execute(const char *file);
	Value print(Token times, Value what);

	// returns ith value from the collection
	Value getAt(Value v, int idx);

	// expression parsers
	Value                 identifierExpression(Token ex);
	Value                 stringExpression(Token ex);
	Value                 numberExpression(Token ex);
	Value                 functionExpression(Token ex);
	static ExpressionRule expressionRules[];

	// expression evaluators
	Result evaluateValue(Value v, int times);
	Result identifierExecute(Value iden, int times);
	Result stringExecute(Value str, int times);
	Result numberExecute(Value num, int times);
	Result functionExecute(TokenType name, Array *args, int times);
#define KEYWORD(x, y, z) \
	Result x##Execute(Result *args, int argc, bool isConstant, int times);
#include "keywords.h"

	// validates whether the given value contains arguments
	// of the same type
	bool validateType(Value arg, Value::Type type);

	static int argumentCounts[];
};

class EngineException : public std::runtime_error {
  private:
	Token       t;
	const char *message;

  public:
	EngineException() : runtime_error("Error occurred while generating!") {}
	EngineException(const char *message)
	    : runtime_error(message), t(Token::PlaceholderToken) {}
	EngineException(Token to, const char *msg)
	    : runtime_error(msg), t(to), message(msg) {}
	virtual const char *what() const throw() {
		t.highlight(true, "At", Token::ERROR);
		return runtime_error::what();
	}
	Token getToken() { return t; }
};
