(function () {
    let recognition;
    let recording = false;

    function toggleVoiceRecording(frm, fields, enable = null) {
        if (enable === null) {
            enable = !frm.voice_recording_enabled;
        }
        frm.voice_recording_enabled = enable;

        const button = $("#voice-record-toggle");

        if (enable) {
            button.text("Disable Voice Recording").css({ 'background-color': 'red', 'color': 'white', 'font-weight': 'bold' });
            showVoiceIcons(frm, fields, true);
        } else {
            button.text("Enable Voice Recording").css({ 'background-color': 'green', 'color': 'white', 'font-weight': 'bold' });
            showVoiceIcons(frm, fields, false);
        }
    }

    function startVoiceRecording(frm, field_name) {
        let SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        recognition.lang = "en";
        recognition.interimResults = true;
        recognition.start();

        recognition.onresult = function (event) {
            const speechResult = event.results[0][0].transcript;
            const currentValue = frm.fields_dict[field_name].get_value() || "";
            if (event.results[0].isFinal) {
                const updatedValue = currentValue + " " + speechResult;
                updateFieldValue(frm, field_name, updatedValue.trim());
            }
        };

        recognition.onspeechend = () => {
            startVoiceRecording(frm, field_name);
        };
    }

    function stopVoiceRecording(frm) {
        if (recognition) {
            recognition.stop();
            recognition = null;
        }
    }

    function updateFieldValue(frm, field_name, value) {
        const field = frm.fields_dict[field_name];

        if (!field) {
            console.error(`Field ${field_name} not found.`);
            return;
        }

        // Check if the field is a Table MultiSelect
        if (field.df.fieldtype === "Table MultiSelect") {
            // Ensure the table is initialized as an array
            if (!Array.isArray(frm.doc[field_name])) {
                frm.doc[field_name] = [];
            }

            // Add a new row in the Table MultiSelect
            let child = frm.add_child(field_name);
            console.log(field_name);
            
            console.log(child);
            child[field_name] = value;  // Replace 'fieldname' with actual child field to store the value
            console.log(child[field_name], "  ", value)
            frm.refresh_field(field_name);
        } else {
            // For normal fields, set the value directly
            frm.set_value(field_name, value);
        }
    }

    function showVoiceIcons(frm, fields, show) {
        fields.forEach((field_name) => {
            const field_wrapper = frm.fields_dict[field_name].$wrapper;
            const field_label = field_wrapper.find(".control-label");

            if (!field_label.find(".voice-icon").length) {
                const icon_html = `
                    <span class="voice-icon" style="margin-left: 8px; cursor: pointer; color: red;">
                        <i class="fa fa-microphone"></i>
                    </span>`;
                field_label.append(icon_html);
            }

            const icon = field_label.find(".voice-icon");
            if (show) {
                icon.show();
            } else {
                icon.hide();
            }

            // Attach event listeners to input fields
            const field = frm.fields_dict[field_name].input;
            $(field).off("focus blur");  // Remove previous event listeners to avoid duplicates
            $(field).on("focus", function () {
                if (frm.voice_recording_enabled) {
                    startVoiceRecording(frm, field_name);
                }
            });
            $(field).on("blur", function () {
                if (frm.voice_recording_enabled) {
                    stopVoiceRecording(frm);
                }
            });
        });
    }

    // Expose functions globally
    window.VoiceRecording = {
        toggleVoiceRecording,
        startVoiceRecording,
        stopVoiceRecording,
        updateFieldValue,
        showVoiceIcons
    };

})();