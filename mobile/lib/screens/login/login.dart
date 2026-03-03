import 'package:flutter/material.dart';
import '../../palette/palette.dart';
import '../dashboard/dashboard_screen.dart';

class Login extends StatefulWidget {
  const Login({super.key});

  @override
  State<Login> createState() => _LoginState();
}

class _LoginState extends State<Login> {
  bool _obscurePassword = true;
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Palette.background_primary,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [

              const SizedBox(height: 50),

              /// ICONA
              Container(
                height: 110,
                width: 110,
                decoration: BoxDecoration(
                  color: Palette.primary,
                  borderRadius: BorderRadius.circular(24),
                ),
                child: const Icon(
                  Icons.school,
                  color: Palette.text_primary,
                  size: 50,
                ),
              ),

              const SizedBox(height: 30),

              /// TITOLO
              const Text(
                "Bentornato!",
                style: TextStyle(
                  fontSize: 28,
                  fontWeight: FontWeight.bold,
                  color: Palette.text_primary,
                ),
              ),

              const SizedBox(height: 8),

              const Text(
                "Accedi al tuo registro elettronico",
                style: TextStyle(
                  fontSize: 16,
                  color: Palette.text_secondary,
                ),
              ),

              const SizedBox(height: 50),

              /// USERNAME
              _buildTextField(
                label: "Username",
                hint: "Inserisci il tuo username",
                icon: Icons.person_outline,
              ),

              const SizedBox(height: 20),

              /// PASSWORD
              _buildTextField(
                label: "Password",
                hint: "Inserisci la tua password",
                icon: Icons.lock_outline,
                isPassword: true,
              ),

              const SizedBox(height: 12),

              Align(
                alignment: Alignment.centerRight,
                child: Text(
                  "Password dimenticata?",
                  style: TextStyle(
                    color: Palette.accent,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ),

              const SizedBox(height: 40),

              /// BOTTONE LOGIN
              SizedBox(
                width: double.infinity,
                height: 55,
                child: ElevatedButton.icon(
                  onPressed: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (context) => DashboardScreen(),
                      )  
                    );
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Palette.primary,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(16),
                    ),
                  ),
                  icon: const Icon(
                    Icons.login,
                    color: Palette.text_primary,
                    size: 20,
                  ),
                  label: const Text(
                    "Accedi con Classeviva",
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w600,
                      color: Palette.text_primary,
                    ),
                  ), 
                ),
              ),

              const Spacer(),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildTextField({
    required String label,
    required String hint,
    required IconData icon,
    bool isPassword = false,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: const TextStyle(
            color: Palette.text_secondary,
            fontSize: 14,
            fontWeight: FontWeight.w500,
          ),
        ),
        const SizedBox(height: 8),
        TextField(
          obscureText: isPassword ? _obscurePassword : false,
          style: const TextStyle(
            color: Palette.text_primary,
            fontSize: 15,
          ),
          cursorColor: Palette.accent,
          decoration: InputDecoration(
            hintText: hint,
            hintStyle: const TextStyle(
              color: Palette.text_tertiary,
              fontSize: 14,
            ),

            /// ICONA SINISTRA
            prefixIcon: Padding(
              padding: const EdgeInsets.only(left: 14, right: 10),
              child: Icon(
                icon,
                size: 20,
                color: Palette.text_tertiary,
              ),
            ),
            prefixIconConstraints:
                const BoxConstraints(minWidth: 40, minHeight: 40),

            /// ICONA DESTRA PASSWORD
            suffixIcon: isPassword
                ? IconButton(
                    icon: Icon(
                      _obscurePassword
                          ? Icons.visibility_outlined
                          : Icons.visibility_off_outlined,
                      size: 20,
                      color: Palette.text_tertiary,
                    ),
                    onPressed: () {
                      setState(() {
                        _obscurePassword = !_obscurePassword;
                      });
                    },
                  )
                : null,

            filled: true,
            fillColor: Palette.background_tertiary,

            contentPadding: const EdgeInsets.symmetric(
              vertical: 18,
              horizontal: 16,
            ),

            /// BORDO NORMALE
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(18),
              borderSide: const BorderSide(
                color: Palette.background_secondary,
                width: 1.2,
              ),
            ),

            /// BORDO FOCUS (EFFETTO PREMIUM)
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(18),
              borderSide: const BorderSide(
                color: Palette.accent,
                width: 1.5,
              ),
            ),
          ),
        ),
      ],
    );
  }
}