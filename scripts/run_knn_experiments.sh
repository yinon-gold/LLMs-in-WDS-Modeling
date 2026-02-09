PROJECT_DIR=.

. "$PROJECT_DIR/.venv/bin/activate"

# LARGE_MODEL=qwen/qwen2.5-vl-72b-instruct
LARGE_MODEL=openai/o3-mini-high
SMALL_MODEL=qwen/qwen-2.5-coder-32b-instruct
N_THREADS=10

# save timestamp
timestamp0=$(date +"%Y-%m-%d_%H:%M:%S")
uv run tests/query_tests.py --network net1 net3 l_town pa --prompt complex --num_retries 3 --large_model $LARGE_MODEL \
    --small_model $SMALL_MODEL -k 0 -t 0.7 --num_threads $N_THREADS --sandbox

timestamp1=$(date +"%Y-%m-%d_%H:%M:%S")
uv run tests/query_tests.py --network net1 net3 l_town pa --prompt complex --num_retries 3 --large_model $LARGE_MODEL \
    --small_model $SMALL_MODEL -k 1 -t 0.7 --num_threads $N_THREADS --sandbox

timestamp2=$(date +"%Y-%m-%d_%H:%M:%S")
uv run tests/query_tests.py --network net1 net3 l_town pa --prompt complex --num_retries 3 --large_model $LARGE_MODEL \
    --small_model $SMALL_MODEL -k 3 -t 0.7 --num_threads $N_THREADS --sandbox

timestamp3=$(date +"%Y-%m-%d_%H:%M:%S")
uv run tests/query_tests.py --network net1 net3 l_town pa --prompt complex --num_retries 3 --large_model $LARGE_MODEL \
    --small_model $SMALL_MODEL -k 5 -t 0.7 --num_threads $N_THREADS --sandbox

timestamp4=$(date +"%Y-%m-%d_%H:%M:%S")
uv run tests/query_tests.py --network net1 net3 l_town pa --prompt complex --num_retries 3 --large_model $LARGE_MODEL \
    --small_model $SMALL_MODEL -k 7 -t 0.7 --num_threads $N_THREADS --sandbox

timestamp5=$(date +"%Y-%m-%d_%H:%M:%S")
uv run tests/query_tests.py --network net1 net3 l_town pa --prompt complex --num_retries 3 --large_model $LARGE_MODEL \
    --small_model $SMALL_MODEL -k 10 -t 0.7 --num_threads $N_THREADS --sandbox

# print all timestamps
echo "Timestamps:"
echo "k=0: $timestamp0"
echo "k=1: $timestamp1"
echo "k=3: $timestamp2"
echo "k=5: $timestamp3"
echo "k=7: $timestamp4"
echo "k=10: $timestamp5"
