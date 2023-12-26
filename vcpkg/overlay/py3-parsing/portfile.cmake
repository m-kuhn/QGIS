set(VCPKG_POLICY_EMPTY_INCLUDE_FOLDER enabled)

set(PY_PACKAGE_NAME "pyparsing")
string(SUBSTRING "${PY_PACKAGE_NAME}" 0 1 PY_PACKAGE_PREFIX)

vcpkg_download_distfile(ARCHIVE
    URLS "https://files.pythonhosted.org/packages/source/${PY_PACKAGE_PREFIX}/${PY_PACKAGE_NAME}/${PY_PACKAGE_NAME}-${VERSION}.tar.gz"
    FILENAME "${PY_PACKAGE_NAME}-${VERSION}.tar.gz"
    SHA512 59ae01e13277e25cabd1a1ea41a27aac9235c09746f54c0eaac53d0aae488309fe2044b3b31e1105cb8207ad3326828ec32bdd5e904cceee8b0d032740679628
)

vcpkg_extract_source_archive(
    SOURCE_PATH
    ARCHIVE ${ARCHIVE}
)

file(GLOB python_versioned LIST_DIRECTORIES true RELATIVE "${CURRENT_INSTALLED_DIR}/lib/" "${CURRENT_INSTALLED_DIR}/lib/python*")
message(STATUS "Building for ${python_versioned}")

set(PYTHON3 "${CURRENT_INSTALLED_DIR}/tools/python3/${python_versioned}")

x_vcpkg_get_python_packages(
    PYTHON_VERSION 3
    PYTHON_EXECUTABLE ${PYTHON3}
    PACKAGES gpep517 flit
    OUT_PYTHON_VAR PYTHON3_FOR_BUILD
)

# Hack ahead: PYTHON3_FOR_BUILD points to the original python binary, not the one in venv (why?)
set(PYTHON3_VENV "${CURRENT_BUILDTREES_DIR}/${TARGET_TRIPLET}-venv")
set(PYTHON3_FOR_BUILD "${CURRENT_BUILDTREES_DIR}/${TARGET_TRIPLET}-venv/bin/${python_versioned}")


# set(WORKING_DIR "${CURRENT_BUILDTREES_DIR}/${TARGET_TRIPLET}-rel/")
# execute_process(
# 	COMMAND mkdir -p "${WORKING_DIR}/"
# )

message(STATUS "Using venv at ${PYTHON3_FOR_BUILD}")

vcpkg_execute_required_process(
	COMMAND "${PYTHON3_VENV}/bin/gpep517" "build-wheel" "--wheel-dir" ".dist" "--output-fd" "2"
        WORKING_DIRECTORY "${SOURCE_PATH}"
        LOGNAME "build-${TARGET_TRIPLET}"
    )

vcpkg_execute_required_process(
	COMMAND "${PYTHON3_FOR_BUILD}" "-m" "installer" "-d" "${CURRENT_PACKAGES_DIR}" "-p" "/" ".dist/${PY_PACKAGE_NAME}-${VERSION}-py3-none-any.whl"
        WORKING_DIRECTORY "${SOURCE_PATH}"
        LOGNAME "install-${TARGET_TRIPLET}"
    )

file(INSTALL "${SOURCE_PATH}/LICENSE" DESTINATION "${CURRENT_PACKAGES_DIR}/share/${PORT}" RENAME copyright)
