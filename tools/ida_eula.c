// ida pro eula management tool
// this program programmatically accepts the end-user license agreement (eula)
// for ida pro on linux, allowing it to run in batch mode without user interaction.
//
// how it works:
// our reverse engineering showed that ida stores its persistent settings,
// including the eula acceptance status, in a registry-like file located at
// ~/.idapro/ida.reg. interactions with this file are handled by an exported
// function in libida.so called 'reg_int_op'.
//
// this tool dynamically loads libida.so at runtime, gets a pointer to the
// reg_int_op function, and then calls it with the correct parameters to either
// read or write the eula acceptance flag. by using ida's own internal api,
// we ensure the setting is modified in a way the application will always recognize.

#include <stdio.h>  // for printf, fprintf
#include <stdlib.h> // for exit
#include <stdint.h> // for standard integer types like int32_t
#include <dlfcn.h>  // for dlopen, dlsym, dlclose (dynamic library loading)
#include <unistd.h> // for getopt (command-line argument parsing)
#include <string.h> // for strcmp

// based on our analysis, this is the function signature for reg_int_op.
// it's a versatile function for both reading and writing integer settings.
//   - key: the name of the setting (e.g., "EULA 90").
//   - mode: a flag that controls behavior. bit 0 (0x1) means 'write', otherwise 'read'.
//   - value: the integer to write, or the default value to return on a failed read.
//   - subkey: an optional secondary key, which we don't need here.
typedef uint64_t (*reg_int_op_t)(const char* key, char mode, int32_t value, const char* subkey);

// a simple struct to hold our program's configuration.
struct tool_config {
  const char* lib_path;
  int query_mode;
  int set_mode;
};

void print_usage(const char* prog_name) {
  fprintf(stderr, "ida pro eula management tool\n");
  fprintf(stderr, "usage: %s [-l /path/to/libida.so] [-q | -s]\n", prog_name);
  fprintf(stderr, "  -l <path>  specify the path to libida.so (default: ./libida.so)\n");
  fprintf(stderr, "  -q         query the current eula acceptance status.\n");
  fprintf(stderr, "  -s         set the eula as accepted.\n\n");
  fprintf(stderr, "note: this tool must be run from a directory where libida.so can find its\n");
  fprintf(stderr, "dependencies, or with ld_library_path configured for the ida directory.\n");
}

void perform_eula_operation(const struct tool_config* config) {
  // the specific key ida uses to store the acceptance status for version 9.x.
  // this was discovered during analysis of the main application binary.
  // future ida versions (e.g., 9.2) will likely use a different key like "EULA 92".
  const char* eula_key = "EULA 90";

  // 1. load the shared library
  // dlopen loads the specified .so file into our process's memory space.
  // this makes its exported functions available to us at runtime.
  // rtld_lazy is an optimization; it resolves symbols only when they're first used.
  printf("attempting to load library: %s\n", config->lib_path);
  void* lib_handle = dlopen(config->lib_path, RTLD_LAZY);
  if (!lib_handle) {
    fprintf(stderr, "error: failed to load %s\n", config->lib_path);
    fprintf(stderr, "dlopen error: %s\n", dlerror());
    fprintf(stderr, "ensure the path is correct and all dependencies are available.\n");
    exit(1);
  }

  // 2. find the function's address (symbol)
  // dlsym looks through the library's symbol table for a function with the name "reg_int_op".
  // if found, it returns the memory address where the function's code begins.
  dlerror(); // clear any previous errors.
  reg_int_op_t reg_int_op_func = (reg_int_op_t) dlsym(lib_handle, "reg_int_op");

  const char* dlsym_error = dlerror();
  if (dlsym_error) {
    fprintf(stderr, "error: failed to find symbol 'reg_int_op' in %s\n", config->lib_path);
    fprintf(stderr, "dlsym error: %s\n", dlsym_error);
    fprintf(stderr, "this could mean you are using a different, incompatible version of ida.\n");
    dlclose(lib_handle);
    exit(1);
  }

  // 3. execute the requested operation
  if (config->query_mode) {
    printf("querying eula status for key: '%s'...\n", eula_key);
    // to read a value, we set mode to 0. the third argument (0) is the default
    // value to return if the key doesn't exist.
    uint64_t result = reg_int_op_func(eula_key, 0, 0, NULL);
    if (result == 1) {
      printf("result: 1 (eula is accepted).\n");
    } else {
      printf("result: 0 (eula is not accepted).\n");
    }
  }

  if (config->set_mode) {
    printf("setting eula status for key: '%s' to accepted...\n", eula_key);
    // to write a value, we set mode to 1. the third argument (1) is the
    // value we want to store, representing 'true' or 'accepted'.
    reg_int_op_func(eula_key, 1, 1, NULL);
    printf("set operation sent. verifying...\n");

    // it's good practice to immediately read the value back to confirm the write worked.
    // a failure here could indicate a problem with file permissions in ~/.idapro/.
    uint64_t result = reg_int_op_func(eula_key, 0, 0, NULL);
    if (result == 1) {
      printf("verification successful: eula is now accepted.\n");
      printf("you should now be able to run ida in batch mode.\n");
    } else {
      fprintf(stderr, "verification failed! eula status is still not accepted.\n");
      fprintf(stderr, "please check permissions for your user's ida config directory (~/.idapro).\n");
    }
  }

  // 4. unload the library
  // dlclose unloads the library, freeing its memory. this also triggers any cleanup
  // routines (atexit handlers) registered by libida.so, which is likely what
  // finalizes the write to the ida.reg file. this is why we see the
  // "thank you for using ida" message, which is printed by one of these handlers.
  dlclose(lib_handle);
  printf("library closed.\n");
}

int main(int argc, char** argv) {
  // initialize config with default values.
  struct tool_config config = {.lib_path = "./libida.so", .query_mode = 0, .set_mode = 0};

  // parse command-line arguments.
  int opt;
  while ((opt = getopt(argc, argv, "l:qs")) != -1) {
    switch (opt) {
    case 'l':
      config.lib_path = optarg;
      break;
    case 'q':
      config.query_mode = 1;
      break;
    case 's':
      config.set_mode = 1;
      break;
    default:
      print_usage(argv[0]);
      return 1;
    }
  }

  // validate that the user specified one and only one action.
  if (!config.query_mode && !config.set_mode) {
    fprintf(stderr, "error: you must specify an action: -q (query) or -s (set).\n\n");
    print_usage(argv[0]);
    return 1;
  }

  if (config.query_mode && config.set_mode) {
    fprintf(stderr, "error: -q and -s are mutually exclusive.\n\n");
    print_usage(argv[0]);
    return 1;
  }

  perform_eula_operation(&config);

  return 0;
}