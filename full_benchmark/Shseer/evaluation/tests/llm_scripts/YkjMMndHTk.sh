
#!/bin/bash

# Create an 8x8 grid to represent the chess board
initialize_board() {
    for ((i=0; i<8; i++)); do
        for ((j=0; j<8; j++)); do
            board[$i,$j]="."
        done
    done
}

# Display the current state of the chess board
display_board() {
    for ((i=0; i<8; i++)); do
        for ((j=0; j<8; j++)); do
            echo -n "${board[$i,$j]} "
        done
        echo
    done
}

# Parse the command line arguments to determine the move
parse_move() {
    local move=$1
    local piece=${move:0:1}
    local from=${move:1:2}
    local to=${move:3:2}

    # Update the board state based on the move
    board[${from:0:1},${from:1:1}]="$piece"
    board[${to:0:1},${to:1:1}]="$piece"
}

# Main function to execute the script
main() {
    initialize_board
    display_board
    parse_move $1
    display_board
}

# Execute the main function with the command line argument
main $1
