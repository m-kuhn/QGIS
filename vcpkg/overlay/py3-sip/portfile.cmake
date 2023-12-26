set(VCPKG_POLICY_EMPTY_INCLUDE_FOLDER enabled)

set(PY_PACKAGE_NAME "sip")
string(SUBSTRING "${PY_PACKAGE_NAME}" 0 1 PY_PACKAGE_PREFIX)

vcpkg_download_distfile(ARCHIVE
    URLS "https://files.pythonhosted.org/packages/source/${PY_PACKAGE_PREFIX}/${PY_PACKAGE_NAME}/${PY_PACKAGE_NAME}-${VERSION}.tar.gz"
    FILENAME "${PY_PACKAGE_NAME}-${VERSION}.tar.gz"
    SHA512 885c32a051e882b82b59bf1365050933f8fc1c619b19f4bc03235edc5741a5e14aae8edf90479ad0283f74ba5c5233a2589c151ec865b130199a6db9800a2294
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
    PACKAGES gpep517 wheel
    OUT_PYTHON_VAR PYTHON3_FOR_BUILD
)

# Hack ahead: PYTHON3_FOR_BUILD points to the original python binary, not the one in venv (why?)
set(PYTHON3_VENV "${CURRENT_BUILDTREES_DIR}/${TARGET_TRIPLET}-venv")
set(PYTHON3_FOR_BUILD "${CURRENT_BUILDTREES_DIR}/${TARGET_TRIPLET}-venv/bin/${python_versioned}")


message(STATUS "Using venv at ${PYTHON3_FOR_BUILD}")

vcpkg_execute_required_process(
	COMMAND "${PYTHON3_VENV}/bin/gpep517" "build-wheel" "--wheel-dir" ".dist" "--output-fd" "2"
        WORKING_DIRECTORY "${SOURCE_PATH}"
        LOGNAME "build-${TARGET_TRIPLET}"
    )

file(GLOB python_wheel RELATIVE "${SOURCE_PATH}" "${SOURCE_PATH}/.dist/*.whl")
message(STATUS "found ${python_wheel} in ${SOURCE_PATH}")
vcpkg_execute_required_process(
	COMMAND "${PYTHON3_FOR_BUILD}" "-m" "installer" "-d" "${CURRENT_PACKAGES_DIR}" "-p" "/" "${python_wheel}"
        WORKING_DIRECTORY "${SOURCE_PATH}"
        LOGNAME "install-${TARGET_TRIPLET}"
    )

execute_process(
    COMMAND mkdir -p "${CURRENT_PACKAGES_DIR}/tools"
)
foreach(TOOL sip-build sip-distinfo sip-install sip-module sip-sdist sip-wheel)
    file(RENAME "${CURRENT_PACKAGES_DIR}/bin/${TOOL}" "${CURRENT_PACKAGES_DIR}/tools/${TOOL}")
endforeach()

file(INSTALL "${SOURCE_PATH}/LICENSE" DESTINATION "${CURRENT_PACKAGES_DIR}/share/${PORT}" RENAME copyright)
