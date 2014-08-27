from django.db import models


class Medico(models.Model):
    id = models.AutoField(primary_key=True, db_column="idMedicoAct")
    nombre = models.CharField("Nombre",max_length=200, db_column="nombreMedicoAct")
    apellido = models.CharField("Apellido",max_length=200, db_column="apellidoMedicoAct")
    #domicilio = models.CharField("Domicilio",max_length=200, db_column="direccionMedico")
    #localidad = models.CharField("Localidad", db_column="localidadMedico",max_length=200)
    #telefono = models.CharField("Telefono",max_length=200, db_column="telMedico")
    #matricula = models.CharField("Matricula",max_length=200, db_column="nroMatricula")
    #mail = models.CharField("Mail",max_length=200, db_column="mail")

    def __unicode__ (self):
        return self.apellido

    class Meta:
        db_table = 'cedirData\".\"tblMedicosAct'


class Usuario(models.Model):
    id = models.AutoField(primary_key=True, db_column="idUsuario")
    nombreUsuario = models.CharField("Nombre Usuario",max_length=200, null=False,blank=False)
    password = models.CharField("Password",max_length=200, null=False,blank=False)
    #idAtorizacion = models.IntegerField()
    medico = models.ForeignKey(Medico, db_column="idMedico")

    class Meta:
        db_table = 'webData\".\"tblUsuarios'


class GrupoUsuarios(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField()

    class Meta:
        db_table = 'webData\".\"gruposUsuarios'


class Linea(models.Model): #Esto que hace aca...
    id = models.AutoField(primary_key=True)
    idCaja = models.IntegerField()
    descripcion = models.CharField()
    monto = models.DecimalField()

    def __unicode__ (self):
        return self.descripcion

    class Meta:
        db_table = 'cedirData\".\"tblCajaMovimientos'


class Paciente(models.Model):
    id = models.AutoField(primary_key=True)
    dni = models.IntegerField()
    nombre = models.CharField(u"Nombre", max_length=200, db_column=u"nombres")
    apellido = models.CharField(u"Apellido", max_length=200)
    edad = models.IntegerField()
    fechaNacimiento = models.DateField()
    domicilio = models.CharField(u"Domicilio", max_length=200, db_column=u"direccion")
    telefono = models.CharField(u"Telefono", max_length=200, db_column=u"tel")
    sexo = models.CharField()
    nroAfiliado = models.CharField(u"Nro", max_length=200)
    email = models.CharField(u'Email', max_length=200, db_column=u"e_mail")

    def get_edad(self):
        return self.id

    class Meta:
        db_table = u'cedirData\".\"tblPacientes'
