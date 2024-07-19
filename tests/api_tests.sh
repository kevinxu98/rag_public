

# controller tests
BASE_URL="http://localhost:8000"  
UPLOAD_FILE_ENDPOINT="/upload_file/"
ASK_QUESTION_ENDPOINT="/ask_question"
SERVICE_STATUS_ENDPOINT="/"
FILE_NAME="file.txt"

# endpoint: /
echo "Testing endpoint: /"
curl -X GET "${BASE_URL}${SERVICE_STATUS_ENDPOINT}"
echo ""

# endpoint: /upload_file/ 
if [ ! -f "${FILE_NAME}" ]; then
    echo "Creating ${FILE_NAME}..."
    echo "This is a test file created on $(date)" > "${FILE_NAME}"
fi

echo "Testing endpoint: /upload_file/"
curl -X POST -F "file=@${FILE_NAME}" "${BASE_URL}${UPLOAD_FILE_ENDPOINT}"
echo ""
rm "${FILE_NAME}"

# endpoint: /ask_question
echo "Testing endpoint: /ask_question"
curl -X POST -H "Content-Type: application/json" -d '{"text": "testing endpoint, reply exactly: successful if connected, else failed to connect"}' "${BASE_URL}${ASK_QUESTION_ENDPOINT}"
echo ""