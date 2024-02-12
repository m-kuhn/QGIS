set(VCPKG_POLICY_EMPTY_INCLUDE_FOLDER enabled)

vcpkg_from_pythonhosted(
    OUT_SOURCE_PATH SOURCE_PATH
    PACKAGE_NAME    PyQt6
    VERSION         ${VERSION}
    SHA512          c2ff8c47c9b0e43c009d0c90f565a54344e6f384c67dd30c2d422465d0702c07713acc0095c8b67827d1146675611c07d548ba282a26e41bb60a0a21977a7a64
)

set(SIPBUILD_ARGS
  "--confirm-license"
  "--qmake" "${CURRENT_INSTALLED_DIR}/tools/Qt6/bin/qmake.exe" #TODO: append .exe only on windows
  "--api-dir" "${CURRENT_PACKAGES_DIR}/share/qt6/qsci/api/python"
  "--verbose"
  "--qt-shared"
  "--no-make"
  "--disable" "QtDesigner"
  "--pep484-pyi"
  "--debug"
  "--target-dir" "${CURRENT_PACKAGES_DIR}/lib/python${PYTHON3_VERSION_MAJOR}.${PYTHON3_VERSION_MINOR}/site-packages"
  "--build-dir" "${CURRENT_BUILDTREES_DIR}/${TARGET_TRIPLET}-rel-build"
)

set(SIPBUILD_ARGS
  "--confirm-license"
  "--qmake" "${CURRENT_INSTALLED_DIR}/tools/Qt6/bin/qmake.exe" #TODO: append .exe only on windows
  "--api-dir" "${CURRENT_PACKAGES_DIR}/share/qt6/qsci/api/python"
  "--verbose"
  "--qt-shared"
  "--no-make"
  "--disable" "QtDesigner"
  "--pep484-pyi"
  #  "--debug" # will create debuggable bindings
  "--target-dir" "${CURRENT_PACKAGES_DIR}/lib/python${PYTHON3_VERSION_MAJOR}.${PYTHON3_VERSION_MINOR}/site-packages"
  "--build-dir" "${CURRENT_BUILDTREES_DIR}/${TARGET_TRIPLET}-rel-build"
)

message(STATUS "Running sipbuild... (${PYTHON3})")
vcpkg_execute_required_process(
        COMMAND "${PYTHON3}" "-m" "sipbuild.tools.build" ${SIPBUILD_ARGS}
        WORKING_DIRECTORY "${SOURCE_PATH}"
        LOGNAME "sipbuild-${TARGET_TRIPLET}-0"
    )
message(STATUS "Running sipbuild...finished.")

# TODO: Can we use vcpkg_install_make here instead of duplicating code?
set(MAKEFILE "${CURRENT_BUILDTREES_DIR}/${TARGET_TRIPLET}-rel-build/Makefile")

vcpkg_list(SET make_opts)
vcpkg_list(SET install_opts)
set(path_backup "$ENV{PATH}")
if (CMAKE_HOST_WIN32)
    vcpkg_add_to_path(PREPEND "${SCRIPTS}/buildsystems/make_wrapper")
    if(NOT DEFINED Z_VCPKG_MAKE)
        vcpkg_acquire_msys(MSYS_ROOT)
        find_program(Z_VCPKG_MAKE make PATHS "${MSYS_ROOT}/usr/bin" NO_DEFAULT_PATH REQUIRED)
    endif()
    set(make_command "${Z_VCPKG_MAKE}")
    vcpkg_list(SET make_opts -j ${VCPKG_CONCURRENCY} --trace -f ${MAKEFILE})

    string(REPLACE " " [[\ ]] vcpkg_package_prefix "${CURRENT_PACKAGES_DIR}")
    string(REGEX REPLACE [[([a-zA-Z]):/]] [[/\1/]] vcpkg_package_prefix "${vcpkg_package_prefix}")
    vcpkg_list(SET install_opts -j ${VCPKG_CONCURRENCY} --trace -f ${MAKEFILE} DESTDIR=${vcpkg_package_prefix}/lib/python${PYTHON3_VERSION_MAJOR}.${PYTHON3_VERSION_MINOR}/site-packages)
    #TODO: optimize for install-data (release) and install-exec (release/debug)

else()
    if(VCPKG_HOST_IS_OPENBSD)
        find_program(Z_VCPKG_MAKE gmake REQUIRED)
    else()
        find_program(Z_VCPKG_MAKE make REQUIRED)
    endif()
    set(make_command "${Z_VCPKG_MAKE}")
    vcpkg_list(SET make_opts V=1 -j ${VCPKG_CONCURRENCY} -f ${MAKEFILE})
    vcpkg_list(SET install_opts -j ${VCPKG_CONCURRENCY} -f ${MAKEFILE} DESTDIR=${CURRENT_PACKAGES_DIR}/lib/python${PYTHON3_VERSION_MAJOR}.${PYTHON3_VERSION_MINOR}/site-packages)

    # To find sip-distinfo and python3 during install
    set(ENV{PATH} "${CURRENT_INSTALLED_DIR}/tools:${CURRENT_INSTALLED_DIR}/tools/python3:$ENV{PATH}")
endif()

vcpkg_list(SET make_cmd_line ${make_command} ${make_opts})
vcpkg_list(SET install_cmd_line ${make_command} install ${install_opts})

message(STATUS "Running build...")
vcpkg_execute_build_process(
        COMMAND ${make_cmd_line}
        WORKING_DIRECTORY "${CURRENT_BUILDTREES_DIR}/${TARGET_TRIPLET}-rel-build"
        LOGNAME "build-${TARGET_TRIPLET}${short_buildtype}"
)
message(STATUS "Running build... finished.")
message(STATUS "Running install...")
vcpkg_execute_build_process(
        COMMAND ${install_cmd_line}
        WORKING_DIRECTORY "${CURRENT_BUILDTREES_DIR}/${TARGET_TRIPLET}-rel-build"
        LOGNAME "install-${TARGET_TRIPLET}${short_buildtype}"
	)
message(STATUS "Running install... finished.")
set(ENV{PATH} "${path_backup}")
