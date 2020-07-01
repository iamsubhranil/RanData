#include <time.h>

#include "CargParser/cargparser.h"
#include <cinttypes>
#include <iostream>

#include "engine.h"

using namespace std;

void printValue(Value v, FILE *f) {
	switch(v.type) {
		case Value::Number: fprintf(f, "%" PRId64, v.as.number); break;
		case Value::String: fprintf(f, "%s", v.as.str->values()); break;
		default: cout << "Invalid type " << v.type << "!\n"; break;
	}
}

void printCollection(CountedCollection c, FILE *f) {
	Collection v = c.c;
	for(int i = 0; i < c.size; i++) {
		printValue(v.at(i), f);
		fprintf(f, "\n");
	}
}

int main(int argc, char *argv[]) {
	ArgumentList args = arg_list_create();

	arg_add(args, 'g', "generate", "Don't output the generated data", false,
	        true);
	arg_add(args, 't', "time", "Measure the time taken to generate the data",
	        false, true);
	arg_add(args, 'p', "process", "Use <value> processes to generate the data",
	        true, true);
	arg_add_positional(args, 'i', "input_file", "File to read from", false);
	arg_add_positional(args, 'o', "output_file",
	                   "File to write to (default is stdout)", true);

	arg_parse(argc, argv, args);

	if(arg_missing_mandatory(args))
		return 1;

	if(arg_is_present(args, 'p')) {
		printf("[Info] Multiprocessing is not yet available!\n");
	}
	Engine e;
	try {
		e.execute("bootstrap.format");
	} catch(EngineException ex) {
		const char *msg = ex.what();
		cout << "[Error] " << msg << "\n";
		cout << "[Warn] Loading bootstrap module failed!\n";
		cout << "[Warn] One or more default rules may not be available!\n";
	}
	clock_t start;
	try {
		if(arg_is_present(args, 't')) {
			start = clock();
		}
		printf("Generating data..\n");
		fflush(stdout);
		CountedCollection v = e.execute(arg_value(args, 'i'));
		if(arg_is_present(args, 't')) {
			printf("Elapsed: %0.6fs\n",
			       (double)(clock() - start) / CLOCKS_PER_SEC);
		}
		if(!arg_is_present(args, 'g')) {
			FILE *f = stdout;
			if(arg_is_present(args, 'o')) {
				f = fopen(arg_value(args, 'o'), "w");
				if(f == NULL) {
					printf("Unable to open '%s' to write!",
					       arg_value(args, 'o'));
					return 2;
				} else {
					printf("Writing to '%s'..\n", arg_value(args, 'o'));
					fflush(stdout);
				}
			}
			printCollection(v, f);
		}
	} catch(EngineException e) {
		const char *m = e.what();
		cout << "[Error] " << m << "\n";
	}
}
