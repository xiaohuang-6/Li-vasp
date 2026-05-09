# Install script for directory: /home/xh121/Li-vasp/local_3060ti_runpack/external/lammps-mace/cmake

# Set the install prefix
if(NOT DEFINED CMAKE_INSTALL_PREFIX)
  set(CMAKE_INSTALL_PREFIX "/home/xh121/Li-vasp/external/lammps-mace-cpu")
endif()
string(REGEX REPLACE "/$" "" CMAKE_INSTALL_PREFIX "${CMAKE_INSTALL_PREFIX}")

# Set the install configuration name.
if(NOT DEFINED CMAKE_INSTALL_CONFIG_NAME)
  if(BUILD_TYPE)
    string(REGEX REPLACE "^[^A-Za-z0-9_]+" ""
           CMAKE_INSTALL_CONFIG_NAME "${BUILD_TYPE}")
  else()
    set(CMAKE_INSTALL_CONFIG_NAME "Release")
  endif()
  message(STATUS "Install configuration: \"${CMAKE_INSTALL_CONFIG_NAME}\"")
endif()

# Set the component getting installed.
if(NOT CMAKE_INSTALL_COMPONENT)
  if(COMPONENT)
    message(STATUS "Install component: \"${COMPONENT}\"")
    set(CMAKE_INSTALL_COMPONENT "${COMPONENT}")
  else()
    set(CMAKE_INSTALL_COMPONENT)
  endif()
endif()

# Install shared libraries without execute permission?
if(NOT DEFINED CMAKE_INSTALL_SO_NO_EXE)
  set(CMAKE_INSTALL_SO_NO_EXE "1")
endif()

# Is this installation the result of a crosscompile?
if(NOT DEFINED CMAKE_CROSSCOMPILING)
  set(CMAKE_CROSSCOMPILING "FALSE")
endif()

# Set default install directory permissions.
if(NOT DEFINED CMAKE_OBJDUMP)
  set(CMAKE_OBJDUMP "/usr/bin/objdump")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/bin/lmp" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/bin/lmp")
    file(RPATH_CHECK
         FILE "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/bin/lmp"
         RPATH "/home/xh121/Li-vasp/external/lammps-mace-cpu/lib:/home/xh121/Li-vasp/external/libtorch-cpu/lib")
  endif()
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/bin" TYPE EXECUTABLE FILES "/home/xh121/Li-vasp/external/lammps-mace-cpu-build/lmp")
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/bin/lmp" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/bin/lmp")
    file(RPATH_CHANGE
         FILE "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/bin/lmp"
         OLD_RPATH "/home/xh121/Li-vasp/external/lammps-mace-cpu-build:/home/xh121/Li-vasp/external/libtorch-cpu/lib:/usr/lib/gcc/x86_64-linux-gnu/12:"
         NEW_RPATH "/home/xh121/Li-vasp/external/lammps-mace-cpu/lib:/home/xh121/Li-vasp/external/libtorch-cpu/lib")
    if(CMAKE_INSTALL_DO_STRIP)
      execute_process(COMMAND "/usr/bin/strip" "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/bin/lmp")
    endif()
  endif()
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/lammps" TYPE FILE FILES "/home/xh121/Li-vasp/local_3060ti_runpack/external/lammps-mace/src/angle.h")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/lammps" TYPE FILE FILES "/home/xh121/Li-vasp/local_3060ti_runpack/external/lammps-mace/src/atom.h")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/lammps" TYPE FILE FILES "/home/xh121/Li-vasp/local_3060ti_runpack/external/lammps-mace/src/bond.h")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/lammps" TYPE FILE FILES "/home/xh121/Li-vasp/local_3060ti_runpack/external/lammps-mace/src/citeme.h")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/lammps" TYPE FILE FILES "/home/xh121/Li-vasp/local_3060ti_runpack/external/lammps-mace/src/comm.h")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/lammps" TYPE FILE FILES "/home/xh121/Li-vasp/local_3060ti_runpack/external/lammps-mace/src/command.h")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/lammps" TYPE FILE FILES "/home/xh121/Li-vasp/local_3060ti_runpack/external/lammps-mace/src/compute.h")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/lammps" TYPE FILE FILES "/home/xh121/Li-vasp/local_3060ti_runpack/external/lammps-mace/src/dihedral.h")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/lammps" TYPE FILE FILES "/home/xh121/Li-vasp/local_3060ti_runpack/external/lammps-mace/src/domain.h")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/lammps" TYPE FILE FILES "/home/xh121/Li-vasp/local_3060ti_runpack/external/lammps-mace/src/error.h")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/lammps" TYPE FILE FILES "/home/xh121/Li-vasp/local_3060ti_runpack/external/lammps-mace/src/exceptions.h")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/lammps" TYPE FILE FILES "/home/xh121/Li-vasp/local_3060ti_runpack/external/lammps-mace/src/fix.h")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/lammps" TYPE FILE FILES "/home/xh121/Li-vasp/local_3060ti_runpack/external/lammps-mace/src/force.h")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/lammps" TYPE FILE FILES "/home/xh121/Li-vasp/local_3060ti_runpack/external/lammps-mace/src/group.h")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/lammps" TYPE FILE FILES "/home/xh121/Li-vasp/local_3060ti_runpack/external/lammps-mace/src/improper.h")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/lammps" TYPE FILE FILES "/home/xh121/Li-vasp/local_3060ti_runpack/external/lammps-mace/src/input.h")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/lammps" TYPE FILE FILES "/home/xh121/Li-vasp/local_3060ti_runpack/external/lammps-mace/src/info.h")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/lammps" TYPE FILE FILES "/home/xh121/Li-vasp/local_3060ti_runpack/external/lammps-mace/src/kspace.h")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/lammps" TYPE FILE FILES "/home/xh121/Li-vasp/local_3060ti_runpack/external/lammps-mace/src/lammps.h")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/lammps" TYPE FILE FILES "/home/xh121/Li-vasp/local_3060ti_runpack/external/lammps-mace/src/lattice.h")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/lammps" TYPE FILE FILES "/home/xh121/Li-vasp/local_3060ti_runpack/external/lammps-mace/src/library.h")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/lammps" TYPE FILE FILES "/home/xh121/Li-vasp/local_3060ti_runpack/external/lammps-mace/src/lmppython.h")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/lammps" TYPE FILE FILES "/home/xh121/Li-vasp/local_3060ti_runpack/external/lammps-mace/src/lmptype.h")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/lammps" TYPE FILE FILES "/home/xh121/Li-vasp/local_3060ti_runpack/external/lammps-mace/src/memory.h")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/lammps" TYPE FILE FILES "/home/xh121/Li-vasp/local_3060ti_runpack/external/lammps-mace/src/modify.h")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/lammps" TYPE FILE FILES "/home/xh121/Li-vasp/local_3060ti_runpack/external/lammps-mace/src/neighbor.h")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/lammps" TYPE FILE FILES "/home/xh121/Li-vasp/local_3060ti_runpack/external/lammps-mace/src/neigh_list.h")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/lammps" TYPE FILE FILES "/home/xh121/Li-vasp/local_3060ti_runpack/external/lammps-mace/src/output.h")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/lammps" TYPE FILE FILES "/home/xh121/Li-vasp/local_3060ti_runpack/external/lammps-mace/src/pair.h")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/lammps" TYPE FILE FILES "/home/xh121/Li-vasp/local_3060ti_runpack/external/lammps-mace/src/platform.h")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/lammps" TYPE FILE FILES "/home/xh121/Li-vasp/local_3060ti_runpack/external/lammps-mace/src/pointers.h")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/lammps" TYPE FILE FILES "/home/xh121/Li-vasp/local_3060ti_runpack/external/lammps-mace/src/region.h")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/lammps" TYPE FILE FILES "/home/xh121/Li-vasp/local_3060ti_runpack/external/lammps-mace/src/timer.h")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/lammps" TYPE FILE FILES "/home/xh121/Li-vasp/local_3060ti_runpack/external/lammps-mace/src/universe.h")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/lammps" TYPE FILE FILES "/home/xh121/Li-vasp/local_3060ti_runpack/external/lammps-mace/src/update.h")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/lammps" TYPE FILE FILES "/home/xh121/Li-vasp/local_3060ti_runpack/external/lammps-mace/src/utils.h")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/lammps" TYPE FILE FILES "/home/xh121/Li-vasp/local_3060ti_runpack/external/lammps-mace/src/variable.h")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/lammps/fmt" TYPE FILE FILES "/home/xh121/Li-vasp/local_3060ti_runpack/external/lammps-mace/src/fmt/core.h")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/lammps/fmt" TYPE FILE FILES "/home/xh121/Li-vasp/local_3060ti_runpack/external/lammps-mace/src/fmt/format.h")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/liblammps.so.0" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/liblammps.so.0")
    file(RPATH_CHECK
         FILE "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/liblammps.so.0"
         RPATH "/home/xh121/Li-vasp/external/lammps-mace-cpu/lib:/home/xh121/Li-vasp/external/libtorch-cpu/lib")
  endif()
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib" TYPE SHARED_LIBRARY FILES "/home/xh121/Li-vasp/external/lammps-mace-cpu-build/liblammps.so.0")
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/liblammps.so.0" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/liblammps.so.0")
    file(RPATH_CHANGE
         FILE "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/liblammps.so.0"
         OLD_RPATH "/home/xh121/Li-vasp/external/libtorch-cpu/lib:/home/xh121/Li-vasp/external/libtorch-cpu/lib/intel64:/home/xh121/Li-vasp/external/libtorch-cpu/lib/intel64_win:/home/xh121/Li-vasp/external/libtorch-cpu/lib/win-x64:/usr/lib/gcc/x86_64-linux-gnu/12:"
         NEW_RPATH "/home/xh121/Li-vasp/external/lammps-mace-cpu/lib:/home/xh121/Li-vasp/external/libtorch-cpu/lib")
    if(CMAKE_INSTALL_DO_STRIP)
      execute_process(COMMAND "/usr/bin/strip" "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/liblammps.so.0")
    endif()
  endif()
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/liblammps.so" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/liblammps.so")
    file(RPATH_CHECK
         FILE "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/liblammps.so"
         RPATH "/home/xh121/Li-vasp/external/lammps-mace-cpu/lib:/home/xh121/Li-vasp/external/libtorch-cpu/lib")
  endif()
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib" TYPE SHARED_LIBRARY FILES "/home/xh121/Li-vasp/external/lammps-mace-cpu-build/liblammps.so")
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/liblammps.so" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/liblammps.so")
    file(RPATH_CHANGE
         FILE "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/liblammps.so"
         OLD_RPATH "/home/xh121/Li-vasp/external/libtorch-cpu/lib:/home/xh121/Li-vasp/external/libtorch-cpu/lib/intel64:/home/xh121/Li-vasp/external/libtorch-cpu/lib/intel64_win:/home/xh121/Li-vasp/external/libtorch-cpu/lib/win-x64:/usr/lib/gcc/x86_64-linux-gnu/12:"
         NEW_RPATH "/home/xh121/Li-vasp/external/lammps-mace-cpu/lib:/home/xh121/Li-vasp/external/libtorch-cpu/lib")
    if(CMAKE_INSTALL_DO_STRIP)
      execute_process(COMMAND "/usr/bin/strip" "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/liblammps.so")
    endif()
  endif()
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/pkgconfig" TYPE FILE FILES "/home/xh121/Li-vasp/external/lammps-mace-cpu-build/liblammps.pc")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/cmake/LAMMPS/LAMMPS_Targets.cmake")
    file(DIFFERENT _cmake_export_file_changed FILES
         "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/cmake/LAMMPS/LAMMPS_Targets.cmake"
         "/home/xh121/Li-vasp/external/lammps-mace-cpu-build/CMakeFiles/Export/0d446439256b72a0ca5e1098049531df/LAMMPS_Targets.cmake")
    if(_cmake_export_file_changed)
      file(GLOB _cmake_old_config_files "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/cmake/LAMMPS/LAMMPS_Targets-*.cmake")
      if(_cmake_old_config_files)
        string(REPLACE ";" ", " _cmake_old_config_files_text "${_cmake_old_config_files}")
        message(STATUS "Old export file \"$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/cmake/LAMMPS/LAMMPS_Targets.cmake\" will be replaced.  Removing files [${_cmake_old_config_files_text}].")
        unset(_cmake_old_config_files_text)
        file(REMOVE ${_cmake_old_config_files})
      endif()
      unset(_cmake_old_config_files)
    endif()
    unset(_cmake_export_file_changed)
  endif()
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/cmake/LAMMPS" TYPE FILE FILES "/home/xh121/Li-vasp/external/lammps-mace-cpu-build/CMakeFiles/Export/0d446439256b72a0ca5e1098049531df/LAMMPS_Targets.cmake")
  if(CMAKE_INSTALL_CONFIG_NAME MATCHES "^([Rr][Ee][Ll][Ee][Aa][Ss][Ee])$")
    file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/cmake/LAMMPS" TYPE FILE FILES "/home/xh121/Li-vasp/external/lammps-mace-cpu-build/CMakeFiles/Export/0d446439256b72a0ca5e1098049531df/LAMMPS_Targets-release.cmake")
  endif()
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/cmake/LAMMPS" TYPE FILE FILES
    "/home/xh121/Li-vasp/external/lammps-mace-cpu-build/LAMMPSConfig.cmake"
    "/home/xh121/Li-vasp/external/lammps-mace-cpu-build/LAMMPSConfigVersion.cmake"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/man/man1" TYPE FILE RENAME "lmp.1" FILES "/home/xh121/Li-vasp/local_3060ti_runpack/external/lammps-mace/doc/lammps.1")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/lammps" TYPE DIRECTORY FILES "/home/xh121/Li-vasp/local_3060ti_runpack/external/lammps-mace/bench")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/lammps" TYPE DIRECTORY FILES "/home/xh121/Li-vasp/local_3060ti_runpack/external/lammps-mace/potentials")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/etc/profile.d" TYPE FILE FILES
    "/home/xh121/Li-vasp/external/lammps-mace-cpu-build/etc/profile.d/lammps.sh"
    "/home/xh121/Li-vasp/external/lammps-mace-cpu-build/etc/profile.d/lammps.csh"
    )
endif()

if(CMAKE_INSTALL_COMPONENT)
  set(CMAKE_INSTALL_MANIFEST "install_manifest_${CMAKE_INSTALL_COMPONENT}.txt")
else()
  set(CMAKE_INSTALL_MANIFEST "install_manifest.txt")
endif()

string(REPLACE ";" "\n" CMAKE_INSTALL_MANIFEST_CONTENT
       "${CMAKE_INSTALL_MANIFEST_FILES}")
file(WRITE "/home/xh121/Li-vasp/external/lammps-mace-cpu-build/${CMAKE_INSTALL_MANIFEST}"
     "${CMAKE_INSTALL_MANIFEST_CONTENT}")
