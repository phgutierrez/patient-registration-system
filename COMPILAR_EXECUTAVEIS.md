## 🔨 Compilar Executáveis .EXE Windows

### OPÇÃO 1: GitHub Actions (Recomendado) ⭐

O GitHub compila automaticamente em servidor Windows.

**Passos:**
1. Já feito! Os arquivos estão no repositório
2. Vá para: https://github.com/phgutierrez/patient-registration-system/actions
3. Clique em "Build Windows Executables"
4. Aguarde completar (~5-10 minutos)
5. Os ZIPs aparecem em "Releases" automaticamente

**Vantagens:**
- Sem instalar nada no seu PC
- Compila em servidor Windows oficial
- Automático e confiável

---

### OPÇÃO 2: PowerShell Script (Windows Local)

Se você tem Windows:

```powershell
# Abra PowerShell como Administrador

cd C:\Caminho\Para\patient-registration-system

pip install -r requirements.txt

.\build_releases.ps1
```

Aguarde 30-40 minutos.

---

### OPÇÃO 3: Manual no Windows

```batch
REM Command Prompt como Administrador
cd C:\Caminho\Para\patient-registration-system

pip install -r requirements.txt
python validate_system.py

REM Compilar 64 bits (15 min)
pyinstaller --clean prontuario_64bits.spec

REM Compilar 32 bits (15 min)
pyinstaller --clean prontuario_32bits.spec

REM Criar ZIPs
cd dist
powershell -Command "Compress-Archive -Path '64bits/prontuario-64bits' -DestinationPath 'prontuario-v1.0.1-64bits.zip' -Force"
powershell -Command "Compress-Archive -Path '32bits/prontuario-32bits' -DestinationPath 'prontuario-v1.0.1-32bits.zip' -Force"
```

---

### Resultado Final

Você terá em `dist/`:
- `prontuario-v1.0.1-64bits.zip` (50-70 MB)
- `prontuario-v1.0.1-32bits.zip` (50-70 MB)

Cada ZIP contém:
- ✅ prontuario-64bits.exe (ou 32bits.exe)
- ✅ Todas as templates HTML
- ✅ CSS e JS do frontend
- ✅ Database schema
- ✅ Python runtime completo

**Quando o usuário baixar e extrair, é só clicar no .exe para usar!**

---

### Próximos Passos

1. Escolha uma opção acima
2. Aguarde compilação
3. Faça upload dos ZIPs para GitHub Release
4. Publicar release

**Recomendação:** Use GitHub Actions (OPÇÃO 1) - é automático!
