import 'package:flutter/material.dart';
import '../palette/palette.dart';

class Login extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Palette.background,
      body: Center(
        child: ConstrainedBox(
          constraints: BoxConstraints(
            maxWidth: 400, // Limita la larghezza del container
          ),
          child: Container(
            padding: EdgeInsets.all(20),
            margin: EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Palette.secondary,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(
                color: Palette.accent,
                width: 2,
              ),
              boxShadow: [
                BoxShadow(
                  color: Palette.accent,
                  blurRadius: 8,
                  offset: Offset(0, 4),
                ),
              ],
            ),
            child: Column(
              mainAxisSize: MainAxisSize.min, // Prende solo lo spazio necessario verticalmente
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(
                  "Log In",
                  style: TextStyle(
                    fontSize: 20, 
                    fontWeight: FontWeight.bold,
                    color: Palette.text,
                  ),
                ),
                SizedBox(height: 12),
                TextField(
                  style: TextStyle(color: Palette.text),
                  obscureText: false,
                  decoration: InputDecoration(
                    labelText: "Codice Personale / Email",
                    labelStyle: TextStyle(color: Palette.text),
                    hintText: "Codice Personale / Email",
                    hintStyle: TextStyle(color: Palette.text),
                    filled: true,
                    fillColor: Palette.primary,
                    enabledBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                      borderSide: BorderSide(
                        color: Colors.black,
                        width: 0,
                      ),
                    ),
                    focusedBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                      borderSide: BorderSide(
                        color: Palette.accent,
                        width: 1,
                      )
                    )
                  ),
                ),
                SizedBox(height: 12),
                TextField(
                  style: TextStyle(color: Palette.text),
                  obscureText: true,
                  decoration: InputDecoration(
                    labelText: "Password",
                    labelStyle: TextStyle(color: Palette.text),
                    hintText: "Password",
                    hintStyle: TextStyle(color: Palette.text),
                    filled: true,
                    fillColor: Palette.primary,
                    enabledBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                      borderSide: BorderSide(
                        color: Colors.black,
                        width: 0,
                      ),
                    ),
                    focusedBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                      borderSide: BorderSide(
                        color: Palette.accent,
                        width: 1,
                      )
                    )
                  ),
                ),
                SizedBox(height: 12),
                FloatingActionButton.extended(
                  onPressed: () => {
                    Navigator.pushNamed(context, '/dashboard'),
                  },
                  icon: Icon(Icons.person, color: Palette.text),
                  label: Text("Entra con le credenziali", style: TextStyle(
                    color: Palette.text,
                  ),),
                  backgroundColor: Palette.primary,
                  elevation: 6,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(16),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}