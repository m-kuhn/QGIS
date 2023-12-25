set(PYTHON3 "${CURRENT_INSTALLED_DIR}/tools/python3/python3.11")

set(WORKING_DIR "${CURRENT_BUILDTREES_DIR}/${TARGET_TRIPLET}-rel/")
execute_process(
	COMMAND mkdir -p "${WORKING_DIR}/"
)

message(STATUS "Running setup install...")
vcpkg_execute_required_process(
	COMMAND "${PYTHON3}" "-m" "pip" "install" "-r" "${CURRENT_PORT_DIR}/requirements.txt" "-t" "${CURRENT_PACKAGES_DIR}/lib/python3.11/site-packages"
	WORKING_DIRECTORY "${WORKING_DIR}"
        LOGNAME "setup-py-install-${TARGET_TRIPLET}"
)
