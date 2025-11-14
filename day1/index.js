const { exec } = require("child_process");

exec("df -h", (error, stdout, stderr) => {
  if (error) {
    console.error(`Error executing command: ${error.message}`);
    return;
  }
  if (stderr) {
    console.error(`Error output: ${stderr}`);
    return;
  }
  console.log(`Disk Space Usage:\n${stdout}`);
});

exec("top -l -n 1", (error, stdout, stderr) => {
  if (error) {
    console.error(`Error executing command: ${error.message}`);
    return;
  }
  if (stderr) {
    console.error(`Error output: ${stderr}`);
    return;
  }
  console.log(`CPU and Memory Usage:\n${stdout}`);
});
