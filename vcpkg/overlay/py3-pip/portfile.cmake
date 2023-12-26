set(VCPKG_POLICY_EMPTY_INCLUDE_FOLDER enabled)

set(PY_PACKAGE_NAME "pip")
string(SUBSTRING "${PY_PACKAGE_NAME}" 0 1 PY_PACKAGE_PREFIX)

vcpkg_download_distfile(ARCHIVE
    URLS "https://files.pythonhosted.org/packages/source/${PY_PACKAGE_PREFIX}/${PY_PACKAGE_NAME}/${PY_PACKAGE_NAME}-${VERSION}.tar.gz"
    FILENAME "${PY_PACKAGE_NAME}-${VERSION}.tar.gz"
    SHA512 b2d8bcff02fe196163e88e02702861bfccba202e5c71d8c6843eeebc84066efa6987574e26a89ff25f096645e99c824dde585fbae415b66d5eb88657bb4d9cb4
)

vcpkg_extract_source_archive(
    SOURCE_PATH
    ARCHIVE ${ARCHIVE}
)

file(GLOB python_versioned LIST_DIRECTORIES true RELATIVE "${CURRENT_INSTALLED_DIR}/lib/" "${CURRENT_INSTALLED_DIR}/lib/python*")
message(STATUS "Building for ${python_versioned}")

set(PYTHON3 "${CURRENT_INSTALLED_DIR}/tools/python3/${python_versioned}")

# x_vcpkg_get_python_packages(
#     PYTHON_VERSION 3
#     PYTHON_EXECUTABLE ${PYTHON3}
#     PACKAGES gpep517 flit
#     OUT_PYTHON_VAR PYTHON3_FOR_BUILD
# )

# Hack ahead: PYTHON3_FOR_BUILD points to the original python binary, not the one in venv (why?)
# set(PYTHON3_VENV "${CURRENT_BUILDTREES_DIR}/${TARGET_TRIPLET}-venv")
# set(PYTHON3_FOR_BUILD "${CURRENT_BUILDTREES_DIR}/${TARGET_TRIPLET}-venv/bin/${python_versioned}")
# 
# 
# message(STATUS "Using venv at ${PYTHON3_FOR_BUILD}")

vcpkg_execute_required_process(
	COMMAND "${PYTHON3}" "setup.py" "build"
        WORKING_DIRECTORY "${SOURCE_PATH}"
        LOGNAME "build-${TARGET_TRIPLET}"
    )

vcpkg_execute_required_process(
	COMMAND "${PYTHON3}" "setup.py" "install" "--root" "${CURRENT_PACKAGES_DIR}" "--prefix=" "--skip-build"
        WORKING_DIRECTORY "${SOURCE_PATH}"
        LOGNAME "install-${TARGET_TRIPLET}"
    )

file(INSTALL "${SOURCE_PATH}/LICENSE" DESTINATION "${CURRENT_PACKAGES_DIR}/share/${PORT}" RENAME copyright)
