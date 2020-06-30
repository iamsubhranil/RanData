#include <time.h>

#include <iostream>

#include "engine.h"

using namespace std;

void printValue(Value v) {
	switch(v.type) {
		case Value::Number: cout << v.as.number; break;
		case Value::String: cout << v.as.str->values(); break;
		default: cout << "Invalid type " << v.type << "!"; break;
	}
}

void printCollection(CountedCollection c) {
	Collection v = c.c;
	for(int i = 0; i < c.size; i++) {
		printValue(v.at(i));
		cout << "\n";
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
		CountedCollection v = e.execute(argv[1]);
		printf("\nElapsed: %0.6fs\n",
		       (double)(clock() - start) / CLOCKS_PER_SEC);
		(void)v;
		// printCollection(v);
	} catch(EngineException e) {
		const char *m = e.what();
		cout << "[Error] " << m << "\n";
	}
}
