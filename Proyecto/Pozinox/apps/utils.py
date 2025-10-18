"""
Utilidades para integración con Supabase Storage
"""
import os
from django.conf import settings
from django.core.files.storage import Storage
from django.core.files.base import ContentFile
from supabase import create_client
import uuid


class SupabaseStorage(Storage):
    """
    Storage backend personalizado para usar Supabase Storage en lugar de almacenamiento local.
    Ideal para el plan gratuito de Supabase.
    """
    
    def __init__(self):
        if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
            raise ValueError("SUPABASE_URL y SUPABASE_KEY deben estar configurados en settings.py")
        
        self.client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        self.bucket_name = 'pozinox-media'  # Nombre del bucket en Supabase
    
    def _save(self, name, content):
        """
        Guarda un archivo en Supabase Storage
        """
        # Generar un nombre único si es necesario
        if self.exists(name):
            name = self.get_available_name(name)
        
        # Leer el contenido del archivo
        if hasattr(content, 'read'):
            file_content = content.read()
        else:
            file_content = content
        
        # Subir a Supabase Storage
        try:
            self.client.storage.from_(self.bucket_name).upload(
                name,
                file_content,
                file_options={"content-type": self._guess_content_type(name)}
            )
            return name
        except Exception as e:
            raise IOError(f"Error al subir archivo a Supabase: {str(e)}")
    
    def _open(self, name, mode='rb'):
        """
        Descarga un archivo desde Supabase Storage
        """
        try:
            response = self.client.storage.from_(self.bucket_name).download(name)
            return ContentFile(response)
        except Exception as e:
            raise IOError(f"Error al descargar archivo de Supabase: {str(e)}")
    
    def delete(self, name):
        """
        Elimina un archivo de Supabase Storage
        """
        try:
            self.client.storage.from_(self.bucket_name).remove([name])
        except Exception as e:
            raise IOError(f"Error al eliminar archivo de Supabase: {str(e)}")
    
    def exists(self, name):
        """
        Verifica si un archivo existe en Supabase Storage
        """
        try:
            files = self.client.storage.from_(self.bucket_name).list()
            return any(f['name'] == name for f in files)
        except:
            return False
    
    def listdir(self, path):
        """
        Lista archivos y directorios en una ruta
        """
        try:
            files = self.client.storage.from_(self.bucket_name).list(path)
            directories = []
            filenames = []
            
            for item in files:
                if item.get('metadata', {}).get('mimetype') == 'application/x-directory':
                    directories.append(item['name'])
                else:
                    filenames.append(item['name'])
            
            return directories, filenames
        except:
            return [], []
    
    def size(self, name):
        """
        Retorna el tamaño de un archivo
        """
        try:
            files = self.client.storage.from_(self.bucket_name).list()
            for f in files:
                if f['name'] == name:
                    return f.get('metadata', {}).get('size', 0)
            return 0
        except:
            return 0
    
    def url(self, name):
        """
        Retorna la URL pública del archivo
        """
        try:
            # Obtener URL pública del archivo
            response = self.client.storage.from_(self.bucket_name).get_public_url(name)
            return response
        except Exception as e:
            return f"{settings.SUPABASE_URL}/storage/v1/object/public/{self.bucket_name}/{name}"
    
    def get_available_name(self, name, max_length=None):
        """
        Genera un nombre único para el archivo
        """
        dir_name, file_name = os.path.split(name)
        file_root, file_ext = os.path.splitext(file_name)
        
        # Agregar UUID al nombre
        unique_name = f"{file_root}_{uuid.uuid4().hex[:8]}{file_ext}"
        
        if dir_name:
            return os.path.join(dir_name, unique_name)
        return unique_name
    
    def _guess_content_type(self, name):
        """
        Adivina el tipo de contenido basado en la extensión del archivo
        """
        import mimetypes
        content_type, _ = mimetypes.guess_type(name)
        return content_type or 'application/octet-stream'


def usar_supabase_storage():
    """
    Función helper para verificar si se debe usar Supabase Storage
    Retorna True si las credenciales de Supabase están configuradas
    """
    return bool(settings.SUPABASE_URL and settings.SUPABASE_KEY)

