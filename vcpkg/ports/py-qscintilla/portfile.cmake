set(VCPKG_BUILD_TYPE release)
set(VCPKG_C_FLAGS "-mmacosx-version-min=11.0")
set(VCPKG_CXX_FLAGS "-mmacosx-version-min=11.0")

vcpkg_download_distfile(ARCHIVE
    URLS "https://www.riverbankcomputing.com/static/Downloads/QScintilla/${VERSION}/QScintilla_src-${VERSION}.tar.gz"
    FILENAME "QScintilla-${VERSION}.tar.gz"
    SHA512 19e2f9e0a14947501c575018df368d24eb7f8c74e74faa5246db36415bf28dc0beee507ed0e73107c02b36a99bbaf55f0ef3349f479d2332e1b92b2c4a32788a
)

vcpkg_extract_source_archive(
    SOURCE_PATH
    ARCHIVE ${ARCHIVE}
    PATCHES
        fix-static.patch
)

file(RENAME "${SOURCE_PATH}/Python/pyproject-qt5.toml" "${SOURCE_PATH}/Python/pyproject.toml")

if(VCPKG_TARGET_IS_WINDOWS)
  set(PY_LIB_DIR "tools/python3/Lib")
else()
  set(PY_LIB_DIR "lib/python${PYTHON3_VERSION_MAJOR}.${PYTHON3_VERSION_MINOR}")
endif()

set(SIPBUILD_ARGS
    "--qmake" "${CURRENT_INSTALLED_DIR}/tools/Qt6/bin/qmake${VCPKG_HOST_EXECUTABLE_SUFFIX}"
    "--api-dir" "${CURRENT_PACKAGES_DIR}/share/Qt6/qsci/api/python"
    "--qsci-features-dir" "${SOURCE_PATH}/src/features"
    "--qsci-include-dir" "${CURRENT_INSTALLED_DIR}/${PY_LIB_DIR}/site-packages/PyQt6/bindings"
    "--qsci-library-dir" "${SOURCE_PATH}/src"
    "--no-make"
    "--verbose"
    "--build-dir" "${CURRENT_BUILDTREES_DIR}/${TARGET_TRIPLET}-rel"
    "--target-dir" "${CURRENT_INSTALLED_DIR}/${PY_LIB_DIR}/site-packages/"
    "--qmake-setting" "QMAKE_MACOSX_DEPLOYMENT_TARGET = 13.0"
)


vcpkg_backup_env_variables(VARS PATH)

vcpkg_add_to_path(PREPEND "${CURRENT_HOST_INSTALLED_DIR}/tools/python3/Scripts/")

message(STATUS "Running sipbuild...")
vcpkg_execute_required_process(
    COMMAND "${PYTHON3}" "-m" "sipbuild.tools.build" ${SIPBUILD_ARGS}
    WORKING_DIRECTORY "${SOURCE_PATH}/Python"
    LOGNAME "sipbuild-${TARGET_TRIPLET}"
)
message(STATUS "Running sipbuild...finished.")

# inventory.txt is consumed by the distinfo tool which is run during make and should be run against the package directory
file(TO_NATIVE_PATH "${CURRENT_INSTALLED_DIR}" NATIVE_INSTALLED_DIR)
vcpkg_replace_string("${CURRENT_BUILDTREES_DIR}/${TARGET_TRIPLET}-rel/inventory.txt"
        "${CURRENT_INSTALLED_DIR}"
        "${CURRENT_PACKAGES_DIR}")
        vcpkg_replace_string("${CURRENT_BUILDTREES_DIR}/${TARGET_TRIPLET}-rel/inventory.txt"
        "${NATIVE_INSTALLED_DIR}"
        "${CURRENT_PACKAGES_DIR}")

vcpkg_qmake_build(SKIP_MAKEFILE BUILD_LOGNAME "install" TARGETS "install")

vcpkg_restore_env_variables(VARS PATH)

vcpkg_python_test_import(MODULE "PyQt6.Qsci")

vcpkg_copy_pdbs()


# Handle copyright
file(INSTALL ${SOURCE_PATH}/LICENSE DESTINATION ${CURRENT_PACKAGES_DIR}/share/${PORT} RENAME copyright)
