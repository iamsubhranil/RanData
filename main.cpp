#include <time.h>

#include <iostream>

#include "engine.h"

using namespace std;

void printValue(Value v) {
	// cout << Value::TypeStrings[v.type] << "\n";
	switch(v.type) {
		case Value::String:
		case Value::Identifier: cout << v.as.str->values(); break;
		case Value::Number: cout << v.as.number; break;
		case Value::Repeat:
			for(int i = 0; i < v.as.rep->size; i++) {
				printValue(v.as.rep->val);
				cout << "\n";
			}
			break;
		case Value::Array:
			for(int i = 0; i < v.as.arr->size; i++) {
				printValue(v.as.arr->at(i));
				cout << "\n";
			}
			break;
		default: cout << "Unknown type " << v.type << "!"; break;
	}
}

int main(int argc, char *argv[]) {
	if(argc < 2) {
		return 1;
	}
	Engine e;
	e.execute("bootstrap.format");
	clock_t start = clock();
	try {
		Value v = e.execute(argv[1]);
		printf("\nElapsed: %0.6fs\n",
		       (double)(clock() - start) / CLOCKS_PER_SEC);
		(void)v;
	} catch(EngineException e) {
		const char *m = e.what();
		cout << "[Error] " << m << "\n";
	}
	// printValue(v);
}
