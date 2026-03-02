import 'package:flutter/material.dart';
import '../palette/palette.dart';

class Login extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
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
          child: Column (
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text("Log In", style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
              SizedBox(height: 12),
              TextField(
                obscureText: false,
                decoration: InputDecoration(
                  labelText: "Codice Personale / Email",
                  hintText: "Codice Personale / Email",
                  filled: true,
                  fillColor: Palette.primary,
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                    borderSide: BorderSide(
                      color: Palette.accent,
                      width: 2,
                    )
                  ),
                ),
              ),
              SizedBox(height: 12),
              TextField(
                obscureText: true,
                decoration: InputDecoration(
                  labelText: "Password",
                  hintText: "Password",
                  filled: true,
                  fillColor: Palette.primary,
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                    borderSide: BorderSide(
                      color: Palette.accent,
                      width: 2,
                    )
                  ),
                ),
              ),
              SizedBox(height: 12),
              FloatingActionButton.extended(
                onPressed: () => {},
                icon: Icon(Icons.person),
                label: Text("Entra con le credenziali"),
                backgroundColor: Palette.primary,
                elevation: 6,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(16),
                ),
              )
            ],
          ),
        ),
      )
    );
  }
}