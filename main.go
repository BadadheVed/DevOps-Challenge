// package main

// import (
// 	"fmt"
// 	"os/exec"
// 	"strings"
// )

// func main() {

// 	claudePathCmd := exec.Command("sh", "-c", "which claude")
// 	outputPath, err := claudePathCmd.CombinedOutput()
// 	if err != nil {
// 		panic(err)
// 	}

// 	cleanPath := strings.TrimSpace(string(outputPath))

// 	fmt.Println("Claude path found:", cleanPath)

// 	cmd := exec.Command(cleanPath, "mcp", "list")
// 	cmd.Dir = "/Users/ved"

// 	output, err := cmd.CombinedOutput()
// 	if err != nil {
// 		fmt.Println("Error Output:", string(output))
// 		panic(err)
// 	}

// 	fmt.Println(string(output))
// }
