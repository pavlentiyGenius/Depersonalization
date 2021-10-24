package com.example.uploadingfiles.cmdrun;

import org.springframework.stereotype.Service;

import java.io.*;

@Service
public class CMDService {

    public void executeCommand(String command) {
        new Thread(new ScriptRunner(command)).start();
    }


    private class ScriptRunner implements Runnable {

        private String command;

        public ScriptRunner(String command) {
            this.command = command;
        }

        @Override
        public void run() {
            File tempScript = createTempScript(command);
            try {
                ProcessBuilder pb = new ProcessBuilder("bash", tempScript.toString());
                pb.inheritIO();
                Process process = pb.start();
                int result = process.waitFor();
                System.out.println(result);
            } catch (IOException | InterruptedException e) {
                e.printStackTrace();
            }
            tempScript.delete();
        }

        public File createTempScript(String command) {
            File tempScript = null;
            Writer streamWriter = null;
            try {
                tempScript = File.createTempFile("script", null);

                streamWriter = new OutputStreamWriter(new FileOutputStream(
                        tempScript));
            } catch (IOException e) {
                e.printStackTrace();
            }
            PrintWriter printWriter = new PrintWriter(streamWriter);
            printWriter.println(command);
            printWriter.close();

            return tempScript;
        }
    }
}
