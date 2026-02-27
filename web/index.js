const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
const synth = window.speechSynthesis;

if (SpeechRecognition && synth) {
    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    const responseDiv = document.getElementById('response');
    recognition.start();

    recognition.onresult = (event) => {
        const transcript = event.results[event.results.length - 1][0].transcript;
        responseDiv.textContent = `You said: ${transcript}`;
        console.log(`Recognized text: ${transcript}`);

        eel.process_command(transcript)(function(response) {
            responseDiv.append(document.createElement('br'));
            const aiResponse = document.createElement('div');
            aiResponse.textContent = `Response from AI: ${response}`;
            responseDiv.append(aiResponse);

            const voices = synth.getVoices();
            if (voices.length > 0) {
                const utterance = new SpeechSynthesisUtterance(response);
                utterance.lang = 'en-US';
                utterance.voice = voices.find(voice => voice.lang === 'en-US') || voices[0];
                synth.speak(utterance);
            } else {
                console.error('No voices available for speech synthesis.');
            }

            recognition.start(); 
        });
    };

    recognition.onerror = (event) => {
        responseDiv.textContent = `Error occurred: ${event.error}`;
        console.error(`Error: ${event.error}`);

        if (event.error === 'no-speech') {
            console.log('No speech detected. Restarting recognition.');
            recognition.start();
        }
    };

    recognition.onend = () => {
        console.log('Recognition ended. Restarting...');
        responseDiv.append(document.createElement('br'));
        const restartMessage = document.createElement('span');
        restartMessage.textContent = 'Listening stopped. Restarting...';
        responseDiv.append(restartMessage);
        recognition.start(); 
    };

    synth.onvoiceschanged = () => {
        const voices = synth.getVoices();
        console.log(voices);
    };

} else {
    console.error('Speech recognition or speech synthesis not supported in this browser.');
}

