CC=g++

OPT = -O3 -Wall
# OPT = -g -Wall

BULLET = ../bullet3-master

CFLAGS = -I $(BULLET)/src/ -std=c++17 -static

LFLAGS =  -std=c++17 
# LFLAGS += -pthread -lstdc++fs -lGL -lGLU
LFLAGS += -pthread -lstdc++fs

LFLAGS += $(BULLET)/bin/libBullet3Common_gmake_x64_release.a
LFLAGS += $(BULLET)/bin/libBulletCollision_gmake_x64_release.a
LFLAGS += $(BULLET)/bin/libBulletDynamics_gmake_x64_release.a
LFLAGS += $(BULLET)/bin/libBulletExampleBrowserLib_gmake_x64_release.a
LFLAGS += $(BULLET)/bin/libLinearMath_gmake_x64_release.a
LFLAGS += $(BULLET)/bin/libOpenGL_Window_gmake_x64_release.a

LFLAGS += -ldl

SRCDIR = ./src
OBJDIR = ./obj
HOMDIR = .

main: object
	@echo
	$(CC) $(OPT) -o $@.exe $(OBJDIR)/*.o -Wl,--start-group $(LFLAGS) -Wl,--end-group
	@echo

object:
	@echo
	@mkdir -p $(OBJDIR)
	$(CC) $(OPT) $(CFLAGS) -c $(SRCDIR)/*.cpp
	@mv -f ./*.o $(OBJDIR)

# When using flags -Wl,--start-group and -Wl,--end-group the compiler resolves dependencies between libraries by going through the libraries multiple times.
# These flags could have severe performance issues in compilation time.

# Utility targets
.PHONY: clean
clean:
	@rm -f *.o *.exe
	@rm -rf $(OBJDIR)

run:
	./main.exe
	cd python_scripts; python3 create_fine_mesh.py --create_cnts --plot_cnts
