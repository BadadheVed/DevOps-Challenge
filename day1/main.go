package main

import (
	"log/slog"
	"os/exec"
)

func main() {
	out, err := exec.Command("df", "-h").CombinedOutput()

	if err != nil {

		slog.Error("Error is ", err)
	}

	slog.Info("Output is ", slog.String("df -h", string(out)))

	out2, err2 := exec.Command("du", "-h").CombinedOutput()

	if err2 != nil {
		slog.Error("Error is ", err2)
	}

	slog.Info("Output is ", slog.String("du -h", string(out2)))
}
