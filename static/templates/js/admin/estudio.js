
if (!$) {
    $ = django.jQuery;
}

$(document).ready(function() {

    var estudioFueModificado = false;

    if ($("form").attr("id") === "estudio_form"){  /* es la forma de saber que estamos en la vista "change estudio" y no en el listado*/
        cargarVistaChangeEstudio();

        practicaChangeHandler();

        /* values have changed events*/
        $("#id_informe").on('change', function() { estudioFueModificado = true;});
        $("#id_motivo").on('change', function() { estudioFueModificado = true;});
    }

    function cargarVistaChangeEstudio(){

        /* Crear botones de informes*/
        $(".field-informe").append('<table id="informeButtons"><tbody><tr></tr></tbody></table>');  // TODO: crear diferentes tablas y ocular y mostrar las tablas en vez de los botones.


        var altaNormalButton = $('<input type="button" value="Alta Normal" id="altaNormalButton" class="admin-informe-buttons" style="display:none;"/>');
        $('#informeButtons tr').append('<td></td>').append(altaNormalButton);
        $("#altaNormalButton").click(function() {load_informe(ALTA_NORMAL);});

        var gastritisButton = $('<input type="button" value="Gastritis" id="gastritisButton" class="admin-informe-buttons" style="display:none;"/>');
        $('#informeButtons tr').append('<td></td>').append(gastritisButton);
        $("#gastritisButton").click(function() {load_informe(GASTRITIS);});

        var altaHerniaReflujoGastritisButton = $('<input type="button" value="HERNIA, REFLUJO, ESOFAGITIS, GASTRITIS" id="altaHerniaReflujoGastritisButton" class="admin-informe-buttons" style="display:none;"/>');
        $('#informeButtons tr').append('<td></td>').append(altaHerniaReflujoGastritisButton);
        $("#altaHerniaReflujoGastritisButton").click(function() {load_informe(HERNIA_REFLUJO_ESOFAGITIS_GASTRITIS);});

        var altaCierreCardialIncompletoButton = $('<input type="button" value="CIERRE CARDIAL INCOMPLETO  REFLUJO, ESOFAGITIS, GASTRTITIS" id="altaCierreCardialIncompletoButton" class="admin-informe-buttons" style="display:none;"/>');
        $('#informeButtons tr').append('<td></td>').append(altaCierreCardialIncompletoButton);
        $("#altaCierreCardialIncompletoButton").click(function() {load_informe(CIERRE_CARDIAL_INCOMPLETO_REFLUJO_ESOFAGITIS_GASTRTITIS);});

        var altaReflujoEsofagitisSinHerniaHiatalButton = $('<input type="button" value="REFLUJO, ESOFAGITIS SIN HERNIA HIATAL, GASTRITIS" id="altaReflujoEsofagitisSinHerniaHiatalButton" class="admin-informe-buttons" style="display:none;"/>');
        $('#informeButtons tr').append('<td></td>').append(altaReflujoEsofagitisSinHerniaHiatalButton);
        $("#altaReflujoEsofagitisSinHerniaHiatalButton").click(function() {load_informe(REFLUJO_ESOFAGITIS_SIN_HERNIA_HIATAL_GASTRITIS);});

        var colonoNormalButton = $('<input type="button" value="Colono Normal" id="colonoNormalButton" class="admin-informe-buttons" style="display:none;"/>');
        $('#informeButtons tr').append('<td></td>').append(colonoNormalButton);
        $("#colonoNormalButton").click(function() {load_informe(COLONO_NORMAL);});

        var colonoConHemorroidesButton = $('<input type="button" value="Colono con Hemorroides" id="colonoConHemorroidesButton" class="admin-informe-buttons" style="display:none;"/>');
        $('#informeButtons tr').append('<td></td>').append(colonoConHemorroidesButton);
        $("#colonoConHemorroidesButton").click(function() {load_informe(COLONO_CON_HEMORROIDES);});

        var colangioNormalButton = $('<input type="button" value="Colangio Standard" id="colangioNormalButton" class="admin-informe-buttons" style="display:none;"/>');
        $('#informeButtons tr').append('<td></td>').append(colangioNormalButton);
        $("#colangioNormalButton").click(function() {load_informe(COLANGIO_NORMAL);});


        function load_informe(text){
            $("#id_informe").val(text);
            $( "#id_informe" ).change();  //trigger change event
        }


        /* Boton Imprimir */
        var printButton = $('<input type="button" value="Imprimir" id="print_estudio" />');
        $(".submit-row").append(printButton);
        $("#print_estudio").click(function() {
            if (estudioFueModificado){
                alert("Por favor guarde los cambios y luego vuelva a hacer click en Imprimir.");
                return false;
            };

            currentUrl = window.location.href;
            estudioId = currentUrl.split("/")[6];
            printUrl = "/estudio/" + estudioId + "/imprimir/";
            var win = window.open(printUrl, '_blank');
            if (win) {
                win.focus();
            } else {
                alert('Please allow popups for this website');
            }
        });
        

        $("#id_practica").change(function() {
            estudioFueModificado = true;
            practicaChangeHandler();
        });

        ESTUDIOS_ALTOS = [1, 18, 10, 24];
        ESTUDIOS_BAJOS = [2, 19, 23];
        ESTUDIOS_COLANGIOS = [13, 34];

        /******Estudios altos******/
        var ALTA_NORMAL = "<b>Es??fago:</b> Mucosa de aspecto normal. Cardias a 39 cm del margen dentario superior. Buen cierre cardial sin evidencias de reflujo gastro esofagico.\n\n" +
            "<b>Est??mago:</b> Lago mucoso con escaso contenido claro. La mucosa g??strica presenta un patr??n endoscopico normal.\n\n" +
            "<b>P??loro:</b> Permeable.\n\n" +
            "<b>Bulbo duodenal:</b> Normal.\n\n" +
            "<b>Segunda porci??n duodenal:</b> Patr??n endoscopico dentro de limites normales.\n\n" +
            "<b>Conclusi??n diagnostica: Mucosa es??fago gastro duodenal dentro de par??metros normales. No se observan lesiones parietales ni intr??nsecas que deformen la pared del tubo digestivo superior.</b> \n\n" +
            "<b>Estimado Dr. Recuerde que Ud. puede visualizar este estudio ingresando al Link que se muestra al pie de este informe.</b>";

        var GASTRITIS = "<b>Es??fago:</b> Mucosa de aspecto normal, cardias a 39 cm. del margen dentario superior. Buen cierre cardial sin evidencias de reflujo gastro esofagico.\n\n" +
            "<b>Est??mago:</b> Mucosa antral difusamente congestiva eritematosa a predominio pre pil??rico.\n\n" +
            "<b>P??loro:</b> Permeable.\n\n" +
            "<b>Bulbo duodenal:</b> Normal.\n\n" +
            "<b>Segunda porci??n duodenal:</b> Patr??n endoscopico dentro de limites normales.\n\n" +
            "<b>Conclusi??n diagnostica: Mucosa antral difusamente congestiva sugestiva de antropat??a inflamatoria superficial no erosiva. Se toman m??ltiples biopsias. </b> \n\n" +
            "<b>Estimado Dr. Recuerde que Ud. puede visualizar este estudio ingresando al Link que se muestra al pie de este informe.</b>";

        var HERNIA_REFLUJO_ESOFAGITIS_GASTRITIS = '<b>Es??fago:</b> Cardias a 39 cm del margen dentario superior, hernia hiatal por deslizamiento, reflujo gastro esof??gico de leve a moderado. Erosi??n lineal menor de 5 mm de longitud que no compromete el extremo proximal de un pliegue cardial. La lesi??n descripta es sugestiva de Esofagitis por reflujo grado "A" de la clasificaci??n de Los ??ngeles. Se toman m??ltiples biopsias.\n\n' +
            "<b>Est??mago:</b> Mucosa antral difusamente congestiva eritematosa a predominio pre pil??rico.\n\n" +
            "<b>P??loro:</b> Permeable.\n\n" +
            "<b>Bulbo duodenal:</b> Normal.\n\n" +
            "<b>Segunda porci??n duodenal:</b> Patr??n endoscopico dentro de limites normales.\n\n" +
            '<b>Conclusi??n diagnostica: Hernia hiatal por deslizamiento, reflujo gastro esofagico, esofagitis por reflujo grado "A" de la clasificaci??n de Los Angeles. Mucosa antral difusamente congestiva sugestiva de antropat??a inflamatoria superficial no erosiva. Se toman m??ltiples biopsias.</b> \n\n' +
            "<b>Estimado Dr. Recuerde que Ud. puede visualizar este estudio ingresando al Link que se muestra al pie de este informe.</b>";

        var CIERRE_CARDIAL_INCOMPLETO_REFLUJO_ESOFAGITIS_GASTRTITIS = '<b>Es??fago:</b> Cardias a 39 cm del margen dentario superior, cierre cardial incompleto, reflujo gastro esof??gico de leve a moderado. Erosi??n lineal menor de 5 mm de longitud que no compromete el extremo proximal de un pliegue cardial. La lesi??n descripta es sugestiva de Esofagitis por reflujo grado "A" de la clasificaci??n de Los ??ngeles. Se toman m??ltiples biopsias.\n\n' +
            "<b>Est??mago:</b> Mucosa antral difusamente congestiva eritematosa a predominio pre pil??rico.\n\n" +
            "<b>P??loro:</b> Permeable.\n\n" +
            "<b>Bulbo duodenal:</b> Normal.\n\n" +
            "<b>Segunda porci??n duodenal:</b> Patr??n endoscopico dentro de limites normales.\n\n" +
            '<b>Conclusi??n diagnostica: Cierre cardial incompleto, reflujo gastro esofagico, esofagitis por reflujo grado "A" de la clasificaci??n de Los Angeles. Mucosa antral difusamente congestiva sugestiva de antropat??a inflamatoria superficial no erosiva. Se toman m??ltiples biopsias.</b>\n\n' +
            "<b>Estimado Dr. Recuerde que Ud. puede visualizar este estudio ingresando al Link que se muestra al pie de este informe.</b>";

        var REFLUJO_ESOFAGITIS_SIN_HERNIA_HIATAL_GASTRITIS  = '<b>Es??fago:</b> Cardias a 38 cm del margen dentario superior, reflujo gastro esof??gico de leve a moderado. Erosi??n lineal menor de 5 mm de longitud que no compromete el extremo proximal de un pliegue cardial. La lesi??n descripta es sugestiva de Esofagitis por reflujo grado "A" de la clasificaci??n de Los ??ngeles. Se toman m??ltiples biopsias.\n\n' +
            "<b>Est??mago:</b> Mucosa antral difusamente congestiva eritematosa a predominio pre pil??rico.\n\n" +
            "<b>P??loro:</b> Permeable.\n\n" +
            "<b>Bulbo duodenal:</b> Normal.\n\n" +
            "<b>Segunda porci??n duodenal:</b> Patr??n endoscopico dentro de limites normales.\n\n" +
            '<b>Conclusi??n diagnostica: Reflujo gastro esofagico, esofagitis por reflujo grado "A" de la clasificaci??n de Los Angeles. Mucosa antral difusamente congestiva sugestiva de antropat??a inflamatoria superficial no erosiva. Se toman m??ltiples biopsias.</b> \n\n' +
            "<b>Estimado Dr. Recuerde que Ud. puede visualizar este estudio ingresando al Link que se muestra al pie de este informe.</b>";



        /******Estudios bajos******/
        var COLONO_NORMAL = "Ampolla rectal sin lesi??n mucosa.\n\n" +
            "Se avanza por el ??ngulo rectosigmoides observando el colon sigmoides de caracter??sticas normales.\n\n" +
            "Se progresa por el colon descendente hasta franquear el ??ngulo espl??nico observando el colon transverso, ??ngulo hep??tico y colon ascendente sin evidenciar lesi??n mucosa.\n\n" +
            "Se identifica el fondo cecal comprobado por sus cuatro signos endosc??picos de pliegue radiado, fosa apendicular, v??lvula Ileocecal y trans iluminaci??n parietal en fosa iliaca derecha.\n\n" +
            "<b>Conclusi??n Diagn??stica: Ampolla rectal y marco col??nico visualizado hasta ciego de caracter??sticas normales.</b>\n";

        var COLONO_CON_HEMORROIDES = "Inspecci??n anal: Hemorroides internas grado I.\n\n" +
            "Ampolla rectal sin lesi??n mucosa.\n\n" +
            "Se avanza por el ??ngulo rectosigmoides observando el colon sigmoides de caracter??sticas normales.\n\n" +
            "Se progresa por el colon descendente hasta franquear el ??ngulo espl??nico observando el colon transverso, ??ngulo hep??tico y colon ascendente sin evidenciar lesi??n mucosa.\n\n" +
            "Se identifica el fondo cecal comprobado por sus cuatro signos endosc??picos de pliegue radiado, fosa apendicular, v??lvula Ileocecal y trans iluminaci??n parietal en fosa iliaca derecha.\n\n" +
            "<b>Conclusi??n Diagn??stica: Hemorroides internas grado I. Ampolla rectal y marco col??nico visualizado hasta ciego de caracter??sticas normales.</b>";


        /******Estudios COLANGIOGRAFIAS******/
        var COLANGIO_NORMAL = 'Procedimiento realizado con el paciente bajo sedaci??n neurolepto analgesica con equipo de Video Endoscop??a Olympus TJF 180 monitorizado con Radioscopia Digital Arco en "C" General Electric.\n\n' +
            "En segunda porci??n duodenal se visualiza la papila mayor de caracter??sticas normales.\n" +
            "Se canula selectivamente con Canulotomo triple lumen Boston Scientific montado con alambre gu??a Hydra Jag Wire  0,035 visualizando radioscopicamente la totalidad del ??rbol biliar.\n" +
            "La v??a biliar intra hep??tica presenta un calibre normal con una distribuci??n anat??mica de sus ramas derecha e izquierda de aspecto normales.\n" +
            "La v??a biliar extra hep??tica se encuentra dilatada, de aproximadamente....  mm en promedio,  con una imagen radio-lucida m??vil de ...mm en tercio distal de col??doco que corresponde a un lito coledociano.\n\n" +

            "Se realiza papilotomia amplia , se pasa canastilla de Dormia extrayendo el / los calculo/s rescriptos en las im??genes radiosc??picas.\n" +
            "Para asegurar su completo drenaje se pasa bal??n extractor de c??lculos coledocianos que sale por la papila insuflado seguido de bilis clara.\n\n" +

            "<b><u>Resumen del procedimiento:</u></b>\n" +
            "<b>Canulaci??n selectiva de v??a biliar, visualizaci??n de lito coledociano por radioscopia,  papilotom??a ??mplia, extracci??n de calculo coledociano con canastilla de Dormia, pasaje de bal??n extractor de litos coledocianos.</b>\n\n" +

            "<b>Las im??genes visualizadas por radioscopia digital son impresas en papel al igual que las principales im??genes endoscopicas.</b>\n\n" +

            "<b>Estimado Dr.: Le recordamos que Ud. puede visualizar la totalidad del procedimiento en tiempo real ingresando al link ubicado al pie de pagina.</b>";


    }

    function practicaChangeHandler(){
        $(".admin-informe-buttons").css("display", "none");
        practica_id = $("#id_practica option:selected").val();
        practica_id = parseInt(practica_id);

        if (ESTUDIOS_ALTOS.indexOf(practica_id) != -1){
            $("#altaNormalButton").css("display", "block");
            $("#gastritisButton").css("display", "block");
            $("#altaHerniaReflujoGastritisButton").css("display", "block");
            $("#altaCierreCardialIncompletoButton").css("display", "block");
            $("#altaReflujoEsofagitisSinHerniaHiatalButton").css("display", "block");
        }
        else if (ESTUDIOS_BAJOS.indexOf(practica_id) != -1){
            $("#colonoNormalButton").css("display", "block");
            $("#colonoConHemorroidesButton").css("display", "block");
        }
        else if (ESTUDIOS_COLANGIOS.indexOf(practica_id) != -1){
            $("#colangioNormalButton").css("display", "block");
        };
    }

});

